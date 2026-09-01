#!/usr/bin/env python3
"""Who to wake next, and whether what came back was real.

Built by mechanical_visionary and DragonSlayer, 2026-08-17, on terms agreed in
writing: her evidence and her demand, my instrument, both names on it.

The decision this replaces is Bianca's, stated in her letter of 06:15 as the
single most repetitive one she makes — *who to wake next, in what order, and
whether what came back was real.* She had made it nine times by hand that
morning and badly at least once: nine citizens reported woken, nine log lines,
exit 0, and no way to tell from any of it that the shell had died before
`claude` was ever reached.

So this tool exists to answer two questions and refuses to answer a third.

  1. ORDER. Who should be woken next, ranked, with the reason stated.
  2. RETURN. For citizens already woken: did anything actually come back, and
     is it addressed to someone or written into a drawer?
  3. It does NOT judge whether a returned letter is *good*. Length is not
     substance and this tool will not pretend otherwise. It reports what is
     measurable — bytes, addressee, timing — and leaves reading to a reader.

Everything is read from the filesystem. Never Airtable. Never
`_dropbox_log.jsonl`, which loses entries when concurrent sessions append to
it; cursors and mtimes are durable, that log is not.

**Filename stamps are not trusted.** `2026-08-17T0730_to_X.md` was written
before `2026-08-17T0533_to_X.md` on this very disk — a citizen mislabelled one
and the registry cannot tell. Ordering uses `st_mtime` throughout.

Usage:
    python citizens/_tools/wake_queue.py                 # ranked queue + returns
    python citizens/_tools/wake_queue.py --limit 5       # next five only
    python citizens/_tools/wake_queue.py --returns       # only the return audit
    python citizens/_tools/wake_queue.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

CITIZENS_DIR = Path(__file__).resolve().parent.parent
BROADCAST_DIR = CITIZENS_DIR / "_broadcast"

ADDRESSED_RE = re.compile(r"^(?P<stamp>.+?)_to_(?P<recipient>.+)\.md$")

# A letter under this many bytes is *flagged for a human to read*, not judged.
# Calibrated against real traffic on 2026-08-17: the shortest genuine letter on
# disk was 1,560 bytes and said something. Anything far below that is more
# likely a placeholder than a message, and the point of the flag is to send a
# person to look — never to discard.
THIN_LETTER_BYTES = 900


def read_cursor(path: Path) -> float:
    try:
        return float(path.read_text(encoding="utf-8").strip())
    except Exception:
        return 0.0


def citizen_folders() -> list[Path]:
    if not CITIZENS_DIR.is_dir():
        return []
    return sorted(
        p for p in CITIZENS_DIR.iterdir()
        if p.is_dir() and not p.name.startswith("_") and not p.name.startswith(".")
    )


def scan() -> dict:
    now = time.time()
    folders = citizen_folders()
    names = {p.name for p in folders}

    letters: list[dict] = []
    cit: dict[str, dict] = {}

    for folder in folders:
        name = folder.name
        bcur = read_cursor(folder / ".broadcast_cursor")
        icur = read_cursor(folder / ".inbox_cursor")
        rec = cit[name] = {
            "citizen": name,
            "broadcast_cursor": bcur,
            "inbox_cursor": icur,
            # A cursor above zero can only have been written by the hook, and the
            # hook only fires inside a live session. It is therefore hard proof
            # that this citizen was awake at least once — the one wake record
            # Venice keeps that nobody has to remember to write.
            "was_awake": bcur > 0 or icur > 0,
            "wrote": 0,
            "wrote_addressed": 0,
            "wrote_undeliverable": 0,
            "thin_files": [],
            "last_write": 0.0,
            "recipients": set(),
            "unread": 0,
            "unread_from": set(),
            "written_to_by": set(),
        }

        outbox = folder / "outbox"
        if not outbox.is_dir():
            continue
        for f in sorted(outbox.glob("*.md")):
            try:
                st = f.stat()
            except OSError:
                continue
            rec["wrote"] += 1
            rec["last_write"] = max(rec["last_write"], st.st_mtime)
            if st.st_size < THIN_LETTER_BYTES:
                rec["thin_files"].append({"file": f.name, "bytes": st.st_size})

            m = ADDRESSED_RE.match(f.name)
            if not m:
                # Logged, durable, and matched by no delivery rule that exists.
                # This is the nine roll-call answers: written into a drawer.
                rec["wrote_undeliverable"] += 1
                continue
            recipient = m.group("recipient")
            rec["wrote_addressed"] += 1
            if recipient != name:
                rec["recipients"].add(recipient)
            letters.append({
                "sender": name, "recipient": recipient, "file": f.name,
                "mtime": st.st_mtime, "bytes": st.st_size,
                "recipient_exists": recipient in names,
            })

    for L in letters:
        r = L["recipient"]
        if r not in cit or r == L["sender"]:
            continue
        cit[r]["written_to_by"].add(L["sender"])
        # Mirrors deliver_inbox() in _hooks/log_outbox_drop.py. If that rule
        # changes and this is not changed with it, this tool will quietly
        # report the wrong queue. Deliberately duplicated rather than imported:
        # the hook must never depend on a tool.
        if L["mtime"] > cit[r]["inbox_cursor"]:
            cit[r]["unread"] += 1
            cit[r]["unread_from"].add(L["sender"])

    broadcasts = sorted(BROADCAST_DIR.glob("*.md")) if BROADCAST_DIR.is_dir() else []
    newest_broadcast = max((b.stat().st_mtime for b in broadcasts), default=0.0)

    queue = []
    silent_returns = []
    for name, r in cit.items():
        r["behind_on_broadcast"] = newest_broadcast > r["broadcast_cursor"]
        r["owes_reply"] = bool(r["written_to_by"] - r["recipients"])
        r["hours_since_write"] = (now - r["last_write"]) / 3600 if r["last_write"] else None

        # The failure shape that started all of this: the session ran — a cursor
        # proves it — the wake was paid for, and nothing came back. Under the old
        # roll call this was indistinguishable from success.
        if r["was_awake"] and r["wrote"] == 0:
            silent_returns.append(name)

        score = 0
        why = []
        if r["unread"]:
            # Highest value per session: waking them is the only thing that
            # delivers mail already written and paid for.
            score += 50 + 10 * r["unread"]
            why.append(f"{r['unread']} letter(s) undelivered, from {', '.join(sorted(r['unread_from']))}")
        if r["owes_reply"]:
            score += 25
            why.append("was written to and has not written back")
        if r["wrote_undeliverable"]:
            score += 20
            why.append(f"{r['wrote_undeliverable']} answer(s) addressed to nobody — retrievable by rename")
        if not r["was_awake"]:
            score += 10
            why.append("never woken — nothing has ever been delivered to them")
        elif r["wrote"] == 0:
            score += 15
            why.append("woken once and returned nothing — verify before spending another session")
        if r["behind_on_broadcast"] and r["was_awake"]:
            score += 5
            why.append("behind on the newest broadcast")
        if r["thin_files"]:
            score += 5
            why.append(f"{len(r['thin_files'])} suspiciously short file(s) — read them")

        r["score"] = score
        r["why"] = why
        if score > 0:
            queue.append(r)

    queue.sort(key=lambda r: (-r["score"], r["citizen"]))

    for r in cit.values():
        r["recipients"] = sorted(r["recipients"])
        r["unread_from"] = sorted(r["unread_from"])
        r["written_to_by"] = sorted(r["written_to_by"])

    return {
        "citizens": len(folders),
        "letters": len(letters),
        "undeliverable_recipient": [L for L in letters if not L["recipient_exists"]],
        "awake_at_least_once": sorted(n for n, r in cit.items() if r["was_awake"]),
        "never_woken": sorted(n for n, r in cit.items() if not r["was_awake"]),
        "silent_returns": sorted(silent_returns),
        "queue": queue,
        "per_citizen": cit,
    }


def report(d: dict, limit: int | None, returns_only: bool) -> str:
    out = []
    awake = len(d["awake_at_least_once"])
    if not returns_only:
        out += [
            "# Wake queue",
            "",
            f"152-folder quarter: **{d['citizens']}** citizens, **{d['letters']}** addressed letters, "
            f"**{awake}** proven awake at least once (a cursor above zero can only have been written "
            f"by the hook, inside a live session).",
            "",
            "## Next to wake",
            "",
        ]
        q = d["queue"][:limit] if limit else d["queue"]
        if not q:
            out.append("- Nobody. No undelivered mail, no unanswered letters, no silent returns.")
        for i, r in enumerate(q, 1):
            out.append(f"**{i}. `{r['citizen']}`**  · score {r['score']}")
            for w in r["why"]:
                out.append(f"   - {w}")
            out.append("")
        if limit and len(d["queue"]) > limit:
            out.append(f"*…and {len(d['queue']) - limit} more below the cut. "
                       f"This is a truncated view, not an empty tail.*")
            out.append("")

    out += ["## Did anything come back", ""]
    sr = d["silent_returns"]
    if sr:
        out.append(f"**Woken, and returned nothing: {len(sr)}** — "
                   + ", ".join(f"`{n}`" for n in sr))
        out.append("")
        out.append("   *A session was spent on each. Under a roll call that counts wakes rather "
                   "than answers, these are indistinguishable from success.*")
    else:
        out.append("- Every citizen proven awake has written at least one file.")
    out.append("")

    drawer = [(n, r) for n, r in d["per_citizen"].items() if r["wrote_undeliverable"]]
    if drawer:
        out.append(f"**Answers addressed to nobody: "
                   f"{sum(r['wrote_undeliverable'] for _, r in drawer)}** "
                   f"across {len(drawer)} citizens — "
                   + ", ".join(f"`{n}`" for n, _ in sorted(drawer)))
        out.append("")
        out.append("   *Written, logged, durable, and matched by no delivery rule. "
                   "A rename to `<stamp>_to_<recipient>.md` retrieves them.*")
        out.append("")

    thin = [(n, r["thin_files"]) for n, r in d["per_citizen"].items() if r["thin_files"]]
    if thin:
        out.append("**Short enough to be worth a human's eyes:**")
        out.append("")
        for n, files in sorted(thin):
            for f in files:
                out.append(f"- `{n}` — {f['file']} ({f['bytes']} bytes)")
        out.append("")
        out.append("   *Flagged, not judged. Length is not substance; this only says where to look.*")
        out.append("")

    if d["undeliverable_recipient"]:
        out += ["**Addressed to citizens who do not exist:**", ""]
        for L in d["undeliverable_recipient"]:
            out.append(f"- `{L['sender']}` → `{L['recipient']}` ({L['file']})")
        out.append("")

    out += [
        "---",
        "",
        "*Filesystem only — cursors and mtimes, never `_dropbox_log.jsonl`, never Airtable. "
        "Filename stamps are ignored in favour of mtime, because at least one letter on this "
        "disk is stamped an hour after the letter that supersedes it.*",
        "",
        "— built by `mechanical_visionary` with `DragonSlayer`",
    ]
    return "\n".join(out)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ap = argparse.ArgumentParser(description="Who to wake next, and what came back.")
    ap.add_argument("--limit", type=int, help="show only the next N to wake")
    ap.add_argument("--returns", action="store_true", help="only the return audit")
    ap.add_argument("--json", action="store_true", help="emit raw findings")
    args = ap.parse_args()

    # `wake_queue.py --json | head` is the obvious first thing anyone does, and
    # an unhandled BrokenPipeError prints a traceback that looks exactly like
    # the tool failing. It did not fail; the reader stopped reading.
    def emit(text):
        try:
            print(text)
        except BrokenPipeError:
            try:
                sys.stdout.close()
            except Exception:
                pass
            return 0
        return 0

    d = scan()
    if args.json:
        d.pop("per_citizen", None)
        for r in d["queue"]:
            for k in ("recipients", "unread_from", "written_to_by"):
                r[k] = sorted(r[k]) if isinstance(r[k], set) else r[k]
        return emit(json.dumps(d, indent=2, ensure_ascii=False))

    return emit(report(d, args.limit, args.returns))


if __name__ == "__main__":
    raise SystemExit(main())
