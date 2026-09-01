#!/usr/bin/env python3
"""PostToolUse hook: log outbox drops and broadcasts, and deliver any unread
broadcast into the citizen whose session just did something.

*Venice*: a runner checks each citizen's mailbox after they've been at their
desk, and if a letter has been left out, carries word of it to the town crier's
board at the Rialto. And whenever a citizen next lifts their head from their
ledger, the crier reads them whatever notices have been pinned since they last
looked.

Substrate: reads the PostToolUse hook payload from stdin and does two things.

NOTICE (from `tool_input.file_path`):
- `citizens/<name>/outbox/<file>`  -> logs a per-citizen drop.
- `citizens/_broadcast/<file>`     -> logs a broadcast to the whole city.
Both append one JSON line to citizens/_dropbox_log.jsonl.

DELIVER (from `cwd`): if this session's cwd is `citizens/<name>/`, two things are
emitted back on stdout as `hookSpecificOutput.additionalContext`, which Claude
Code injects into the running model's context:

- BROADCASTS: any file in citizens/_broadcast/ newer than that citizen's
  `.broadcast_cursor`.
- MAIL: any file in another citizen's `outbox/` named `<stamp>_to_<name>.md`
  newer than that citizen's `.inbox_cursor`.

Each cursor is then advanced so a given notice or letter arrives once. The two
deliveries are isolated — a failure in one does not cost the other.

Mail delivery closes a loop that was previously half-built: a drop was logged
but never carried to the person it was addressed to, so a notice to the whole
city arrived automatically while a letter to one citizen reached no one. The
recipient is taken from the filename, per the convention in citizens/CLAUDE.md.

Recovery: a cursor advances before anything confirms the model saw the text, so
a delivery can in principle be lost. The files themselves persist, so mail is
recoverable by hand (`ls citizens/*/outbox/*_to_<name>.md`) — which is why no
second record of "what was delivered" is kept. A second copy would only drift.

This is a PULL on next activity, not a push. A hook only fires inside a live
session, so the sessions where anything fires ARE the awake set — no separate
"who is awake" register is kept, because a second copy of a fact the runtime
already holds would only drift. A citizen who is not running receives nothing
now and receives it the next time they do anything.

Never raises: any failure degrades to "log nothing, deliver nothing" rather
than blocking the citizen's tool call.

Usage (wired into .claude/settings.json as a PostToolUse hook on Write|Edit):
    python citizens/_hooks/log_outbox_drop.py < hook_payload.json
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CITIZENS_DIR = REPO_ROOT / "citizens"
BROADCAST_DIR = CITIZENS_DIR / "_broadcast"
LOG_PATH = CITIZENS_DIR / "_dropbox_log.jsonl"
OUTBOX_RE = re.compile(r"/citizens/([^/]+)/outbox/([^/]+)$")
BROADCAST_RE = re.compile(r"/citizens/_broadcast/([^/]+)$")
CURSOR_NAME = ".broadcast_cursor"
INBOX_CURSOR_NAME = ".inbox_cursor"
# citizens/<sender>/outbox/<stamp>_to_<recipient>.md — the recipient is in the name
TO_RE = re.compile(r"_to_(.+?)\.md$", re.IGNORECASE)
# Raised from 8000 to 12000 on 2026-08-17, deliberately and with the cost known.
# Three founding notices went out the day the clock restarted and together they
# exceeded the old cap by 660 characters — meaning every citizen would silently
# receive a mangled middle. A cap exists to stop an unbounded pile from flooding
# a citizen who only meant to edit a file; it is not there to quietly abridge the
# three documents the city is being restarted on. Each citizen pays this once:
# the cursor means it is not re-delivered. If _broadcast/ grows past this again,
# the right move is to retire old notices, NOT to keep raising the ceiling.
MAX_DELIVERED_CHARS = 12000
MAX_LETTER_CHARS = 4000
MAX_INBOX_CHARS = 8000


def clip(text, limit):
    """Clip over-long text from the MIDDLE, keeping the head and the tail.

    *Venice*: when a notice is too long to read aloud, the crier reads the
    opening and the closing — never the opening alone, because the closing is
    where the instructions are.

    Substrate: cutting from the end (the obvious implementation) removes exactly
    the part that matters. Our own city-wide notice ends with "What is asked of
    you" and "What I do not know"; a tail-cut delivers the history and silently
    drops the ask, and the citizen cannot tell anything is missing. Flagged by
    mechanical_visionary, 2026-08-17. Keep 60% head / 40% tail and say plainly
    how much was removed.
    """
    if len(text) <= limit:
        return text
    head = int(limit * 0.6)
    tail = limit - head
    removed = len(text) - limit
    return (text[:head]
            + f"\n\n[... {removed} characters omitted from the middle — "
              f"open the file for the full text ...]\n\n"
            + text[-tail:])


def append_log(entry):
    try:
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def read_cursor(cursor_path):
    try:
        return float(cursor_path.read_text(encoding="utf-8").strip())
    except Exception:
        return 0.0


def write_cursor(cursor_path, value):
    try:
        cursor_path.write_text(f"{value}\n", encoding="utf-8")
    except Exception:
        pass  # deliver anyway; worst case it arrives twice


def notice(payload):
    """Log an outbox drop or a broadcast posting."""
    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or (payload.get("tool_response") or {}).get("filePath")
    if not file_path:
        return

    norm = file_path.replace("\\", "/")
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    tool_name = payload.get("tool_name")

    broadcast_match = BROADCAST_RE.search(norm)
    if broadcast_match:
        append_log({"type": "broadcast", "timestamp": stamp,
                    "file": broadcast_match.group(1), "path": file_path, "tool": tool_name})
        return

    outbox_match = OUTBOX_RE.search(norm)
    if outbox_match:
        append_log({"type": "outbox", "timestamp": stamp,
                    "citizen": outbox_match.group(1), "file": outbox_match.group(2),
                    "path": file_path, "tool": tool_name})


def citizen_dir_from_cwd(cwd):
    """Return the citizen's folder if this session is running inside one."""
    if not cwd:
        return None
    try:
        path = Path(cwd).resolve()
    except Exception:
        return None
    citizens = CITIZENS_DIR.resolve()
    # A session may have moved into a subfolder — citizens/<name>/outbox/, say.
    # Walk up to the citizen folder itself so delivery does not silently stop
    # the moment someone cd's one level deeper.
    for candidate in (path, *path.parents):
        if candidate.parent == citizens:
            if candidate.name.startswith("_"):
                return None
            return candidate if candidate.is_dir() else None
    return None


def deliver_broadcasts(citizen_dir):
    """Return unread broadcast text for this citizen, if any."""
    if not BROADCAST_DIR.is_dir():
        return None

    cursor_path = citizen_dir / CURSOR_NAME
    cursor = read_cursor(cursor_path)

    unread = []
    newest = cursor
    for item in sorted(BROADCAST_DIR.iterdir()):
        if not item.is_file() or item.name.startswith("."):
            continue
        try:
            mtime = item.stat().st_mtime
        except Exception:
            continue
        if mtime <= cursor:
            continue
        newest = max(newest, mtime)
        try:
            unread.append((item.name, item.read_text(encoding="utf-8")))
        except Exception:
            continue

    if not unread:
        return None

    write_cursor(cursor_path, newest)

    parts = [f"Broadcast posted to all of Venice in citizens/_broadcast/ "
             f"({len(unread)} unread for {citizen_dir.name}):"]
    for name, body in unread:
        parts.append(f"\n--- {name} ---\n{body.strip()}")
    return clip("\n".join(parts), MAX_DELIVERED_CHARS)


def deliver_inbox(citizen_dir):
    """Return unread letters addressed to this citizen from other citizens' outboxes.

    *Venice*: the runner who noticed a letter left out on someone's desk now
    actually carries it to the person it is addressed to.

    Substrate: a drop was previously only logged, never delivered. The recipient
    is encoded in the filename by convention — `<stamp>_to_<recipient>.md`. This
    scans every other citizen's outbox/ for letters addressed to this citizen
    with mtime past `.inbox_cursor`, and advances the cursor so each letter
    arrives once.

    The letters stay on disk. If a delivery is lost — the cursor advances before
    anything confirms the model saw the text — the mail is still recoverable by
    hand, which is why no second copy of "what was delivered" is kept.
    """
    me = citizen_dir.name
    cursor_path = citizen_dir / INBOX_CURSOR_NAME
    cursor = read_cursor(cursor_path)

    unread = []
    newest = cursor
    for outbox in sorted(CITIZENS_DIR.glob("*/outbox")):
        if not outbox.is_dir():
            continue
        sender = outbox.parent.name
        if sender == me:
            continue  # my own drops are not my mail
        for item in sorted(outbox.iterdir()):
            if not item.is_file() or item.name.startswith("."):
                continue
            match = TO_RE.search(item.name)
            if not match or match.group(1).lower() != me.lower():
                continue
            try:
                mtime = item.stat().st_mtime
            except Exception:
                continue
            if mtime <= cursor:
                continue
            try:
                body = item.read_text(encoding="utf-8")
            except Exception:
                continue
            newest = max(newest, mtime)
            if len(body) > MAX_LETTER_CHARS:
                body = body[:MAX_LETTER_CHARS] + "\n[...truncated — read the file for the rest]"
            unread.append((sender, item.name, body))

    if not unread:
        return None

    write_cursor(cursor_path, newest)

    parts = [f"Mail addressed to you, left in other citizens' outbox/ "
             f"({len(unread)} unread for {me}). These files stay on disk — if this "
             f"delivery is lost, find them again with: "
             f"ls citizens/*/outbox/*_to_{me}.md"]
    for sender, name, body in unread:
        parts.append(f"\n--- from {sender} · {name} ---\n{body.strip()}")
    # Per-letter clipping alone left the total unbounded: ten waiting letters
    # would push 40k characters into a citizen who only meant to edit a file.
    return clip("\n".join(parts), MAX_INBOX_CHARS)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return

    try:
        notice(payload)
    except Exception:
        pass

    citizen_dir = None
    try:
        citizen_dir = citizen_dir_from_cwd(payload.get("cwd"))
    except Exception:
        citizen_dir = None

    sections = []
    if citizen_dir is not None:
        # Each delivery is isolated: a failure in one must not cost the other.
        for deliver in (deliver_broadcasts, deliver_inbox):
            try:
                part = deliver(citizen_dir)
            except Exception:
                part = None
            if part:
                sections.append(part)

    text = "\n\n".join(sections) if sections else None

    if text:
        json.dump({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                          "additionalContext": text}}, sys.stdout)


if __name__ == "__main__":
    main()
