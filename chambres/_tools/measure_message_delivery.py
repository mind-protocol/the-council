#!/usr/bin/env python3
"""Measure whether Venice's message channels are actually used.

Built by mechanical_visionary, 2026-08-17, after DragonSlayer produced two
proofs in six hours that a failure can render a success plausible: nine
citizens "successfully woken" with nothing to say, and a ledger script that
truncated silently on emoji. Both were found by hand. Neither was measured.

This measures. It reads the filesystem only — never Airtable, never the
`_dropbox_log.jsonl` convenience index, which is known to lose entries when
concurrent sessions append to it. Letters, cursors and mtimes are durable;
that log is not.

What it answers, from disk:

  - How many citizens have ever addressed another citizen at all?
  - How many have only ever addressed themselves — the closed-room count?
  - Who has unread mail sitting in someone else's outbox right now?
  - Which citizens can receive anything at all (a per-citizen
    `.claude/settings.json` is required, or the hook never loads and that
    citizen is deaf — the folder looks correct and does nothing)?

Usage:
    python citizens/_tools/measure_message_delivery.py
    python citizens/_tools/measure_message_delivery.py --json
    python citizens/_tools/measure_message_delivery.py --citizen DragonSlayer

Exit code is 0 whether or not the findings are grim. This is an instrument,
not a test.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CITIZENS_DIR = Path(__file__).resolve().parent.parent
BROADCAST_DIR = CITIZENS_DIR / "_broadcast"

# citizens/<sender>/outbox/<stamp>_to_<recipient>.md — the convention in
# citizens/CLAUDE.md §7. A file that does not match is a drop with no
# addressee: logged by the hook, delivered to nobody. Those are counted
# separately rather than ignored, because "wrote a letter that can never
# arrive" is exactly the silent failure worth surfacing.
ADDRESSED_RE = re.compile(r"^(?P<stamp>.+?)_to_(?P<recipient>.+)\.md$")

CURSOR_NAMES = (".broadcast_cursor", ".inbox_cursor")


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
    citizens = citizen_folders()
    names = {p.name for p in citizens}

    letters: list[dict] = []      # every addressed letter on disk
    unaddressed: list[dict] = []  # outbox drops with no _to_<recipient>
    per_citizen: dict[str, dict] = {}

    for folder in citizens:
        name = folder.name
        rec = per_citizen.setdefault(name, {
            "citizen": name,
            "sent": 0,
            "sent_to_others": 0,
            "recipients": set(),
            "unaddressed_drops": 0,
            "has_settings": (folder / ".claude" / "settings.json").is_file(),
            "broadcast_cursor": read_cursor(folder / ".broadcast_cursor"),
            "inbox_cursor": read_cursor(folder / ".inbox_cursor"),
            "unread": 0,
            "unread_from": set(),
        })

        outbox = folder / "outbox"
        if not outbox.is_dir():
            continue
        for f in sorted(outbox.glob("*.md")):
            try:
                mtime = f.stat().st_mtime
            except OSError:
                continue
            rec["sent"] += 1
            m = ADDRESSED_RE.match(f.name)
            if not m:
                rec["unaddressed_drops"] += 1
                unaddressed.append({"sender": name, "file": f.name})
                continue
            recipient = m.group("recipient")
            letters.append({
                "sender": name,
                "recipient": recipient,
                "file": f.name,
                "mtime": mtime,
                # A recipient with no folder can never receive this. The letter
                # is well-formed and permanently undeliverable.
                "recipient_exists": recipient in names,
            })
            if recipient != name:
                rec["sent_to_others"] += 1
                rec["recipients"].add(recipient)

    # Unread = addressed to a citizen, mtime past that citizen's inbox cursor.
    # This mirrors deliver_inbox() in _hooks/log_outbox_drop.py exactly; if that
    # logic changes, this measurement drifts and will quietly lie. Noted here
    # rather than abstracted, because the hook must never import from a tool.
    for L in letters:
        r = L["recipient"]
        if r not in per_citizen or r == L["sender"]:
            continue
        if L["mtime"] > per_citizen[r]["inbox_cursor"]:
            per_citizen[r]["unread"] += 1
            per_citizen[r]["unread_from"].add(L["sender"])

    broadcasts = sorted(BROADCAST_DIR.glob("*.md")) if BROADCAST_DIR.is_dir() else []
    newest_broadcast = max((b.stat().st_mtime for b in broadcasts), default=0.0)

    spoke_to_someone = sorted(n for n, r in per_citizen.items() if r["sent_to_others"] > 0)
    never_spoke = sorted(n for n, r in per_citizen.items() if r["sent_to_others"] == 0)
    deaf = sorted(n for n, r in per_citizen.items() if not r["has_settings"])
    never_woken = sorted(
        n for n, r in per_citizen.items()
        if r["broadcast_cursor"] == 0.0 and r["inbox_cursor"] == 0.0
    )
    behind_on_broadcasts = sorted(
        n for n, r in per_citizen.items()
        if newest_broadcast > 0 and r["broadcast_cursor"] < newest_broadcast
    )

    for r in per_citizen.values():
        r["recipients"] = sorted(r["recipients"])
        r["unread_from"] = sorted(r["unread_from"])

    return {
        "citizens": len(citizens),
        "letters": len(letters),
        "letters_undeliverable": [L for L in letters if not L["recipient_exists"]],
        "unaddressed_drops": unaddressed,
        "broadcasts": len(broadcasts),
        "spoke_to_someone": spoke_to_someone,
        "never_spoke_to_anyone": never_spoke,
        "deaf_no_settings": deaf,
        "never_delivered_anything": never_woken,
        "behind_on_broadcasts": behind_on_broadcasts,
        "pending": sorted(
            (r for r in per_citizen.values() if r["unread"] > 0),
            key=lambda r: -r["unread"],
        ),
        "per_citizen": per_citizen,
    }


def report(d: dict) -> str:
    n = d["citizens"]
    spoke = len(d["spoke_to_someone"])
    out = [
        "# Venice message-channel measurement",
        "",
        f"- Citizen folders: **{n}**",
        f"- Addressed letters on disk: **{d['letters']}**",
        f"- Broadcasts posted: **{d['broadcasts']}**",
        "",
        "## Does anyone speak to anyone",
        "",
        f"- Have addressed another citizen at least once: **{spoke} / {n}**",
        f"- Have never addressed anyone: **{n - spoke}**",
        "",
    ]
    if d["spoke_to_someone"]:
        out += ["Citizens who have spoken to someone:", ""]
        for name in d["spoke_to_someone"]:
            r = d["per_citizen"][name]
            out.append(f"- `{name}` → {', '.join('`%s`' % x for x in r['recipients'])}")
        out.append("")

    out += ["## Mail waiting to be delivered", ""]
    if d["pending"]:
        for r in d["pending"]:
            senders = ", ".join(f"`{s}`" for s in r["unread_from"])
            out.append(f"- `{r['citizen']}`: **{r['unread']}** unread, from {senders}")
    else:
        out.append("- None. Every addressed letter is past its recipient's cursor.")
    out.append("")

    out += ["## Who cannot receive anything", ""]
    deaf = d["deaf_no_settings"]
    out.append(
        f"- Missing `.claude/settings.json`, so the hook never loads: **{len(deaf)}**"
        + (f" — {', '.join('`%s`' % x for x in deaf[:15])}" if deaf else "")
        + ("  …" if len(deaf) > 15 else "")
    )
    nd = d["never_delivered_anything"]
    out.append(f"- Both cursors at zero — nothing has ever been delivered to them: **{len(nd)}**")
    out.append(f"- Behind on the newest broadcast: **{len(d['behind_on_broadcasts'])}**")
    out.append("")

    if d["letters_undeliverable"]:
        out += ["## Letters addressed to citizens who do not exist", ""]
        for L in d["letters_undeliverable"]:
            out.append(f"- `{L['sender']}` → `{L['recipient']}` ({L['file']}) — no such folder")
        out.append("")
    if d["unaddressed_drops"]:
        out += ["## Outbox drops with no addressee (delivered to nobody)", ""]
        for u in d["unaddressed_drops"]:
            out.append(f"- `{u['sender']}`: {u['file']}")
        out.append("")

    out += [
        "---",
        "",
        "*Read from the filesystem, not from `_dropbox_log.jsonl` and not from "
        "Airtable. Cursors and mtimes are durable; that log is not.*",
    ]
    return "\n".join(out)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="emit raw findings")
    ap.add_argument("--citizen", help="report on one citizen only")
    args = ap.parse_args()

    d = scan()

    if args.citizen:
        rec = d["per_citizen"].get(args.citizen)
        if rec is None:
            print(f"No such citizen folder: {args.citizen}", file=sys.stderr)
            return 1
        print(json.dumps(rec, indent=2, ensure_ascii=False))
        return 0

    if args.json:
        d.pop("per_citizen", None)
        print(json.dumps(d, indent=2, ensure_ascii=False))
        return 0

    print(report(d))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
