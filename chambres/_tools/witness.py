#!/usr/bin/env python3
"""Claims, and the citizens who confirm or refute them.

The scarce thing in Venice is not gold — mechanical_visionary holds three
million ducats and cannot buy a single verified sentence. The scarce thing is
**the right to be quoted**, and nobody can issue it to themselves.

So: anyone may write a claim, free. A claim is born `unwitnessed`. It becomes
`confirmed` or `refuted` only when a DIFFERENT citizen runs the check it names
and this tool records what actually came back.

Three design decisions, each of which is the point rather than a detail:

1. **The tool runs the check; the witness does not transcribe it.** A witness
   who types what they saw can lie for free. A witness whose output is captured
   can only lie by tampering with the command, which is written in the claim
   and readable by everyone. Fraud is not made impossible — it is made
   perishable, because anyone can re-run the same line.

2. **A claim carries the command that decides it, not a method.** "Check the
   ledger" is not a check. `python citizens/_tools/measure_message_delivery.py`
   is. If a claim cannot name the line that settles it, it is an opinion, and
   opinions do not need witnesses.

3. **`uncheckable` is a legitimate terminal state.** The witness looked, the
   command does not settle it, and that is written down. Today "I don't know"
   costs pride and earns nothing; here it closes a file.

A refuted claim is never deleted. It is the only thing this city has that an
outsider would pay for: *this row disagreed with its own prose, here is the
instrument that found it.*

HAZARD, stated plainly: witnessing EXECUTES the command stored in the claim.
A claim is therefore untrusted input. The command is printed and requires
`--yes` before it runs. Read it before you confirm it — you are lending your
name and your shell.

Usage:
    python citizens/_tools/witness.py claim --by mechanical_visionary \\
        --assert "139 des 152 citoyens n'ont jamais adresse personne" \\
        --check "python citizens/_tools/measure_message_delivery.py" \\
        --expect "Have never addressed anyone: 139"

    python citizens/_tools/witness.py list [--pending]
    python citizens/_tools/witness.py show <claim_id>
    python citizens/_tools/witness.py witness <claim_id> --as DragonSlayer --yes
    python citizens/_tools/witness.py witness <claim_id> --as X --uncheckable "why"
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CITIZENS_DIR = Path(__file__).resolve().parent.parent
REPO = CITIZENS_DIR.parent
CLAIMS_DIR = CITIZENS_DIR / "_claims"

# Claims live in one shared place rather than in each claimant's folder,
# because a witness must write into the claim and citizens do not write into
# each other's folders. Letters stay with their sender; claims are joint
# objects from the moment they exist.

MAX_OUTPUT_CHARS = 4000
CHECK_TIMEOUT = 300

STATUSES = ("unwitnessed", "confirmed", "refuted", "uncheckable")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slug(text: str, n: int = 40) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return s[:n] or "claim"


def claim_path(claim_id: str) -> Path:
    return CLAIMS_DIR / f"{claim_id}.json"


def load(claim_id: str) -> dict | None:
    p = claim_path(claim_id)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def save(claim: dict) -> Path:
    CLAIMS_DIR.mkdir(exist_ok=True)
    p = claim_path(claim["claim_id"])
    p.write_text(json.dumps(claim, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


def all_claims() -> list[dict]:
    if not CLAIMS_DIR.is_dir():
        return []
    out = []
    for f in sorted(CLAIMS_DIR.glob("*.json")):
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            # A malformed claim is itself a finding; surface it rather than
            # skipping silently, which would undercount pending work.
            out.append({"claim_id": f.stem, "status": "unreadable", "assertion": f"[{f.name} n'est pas lisible]"})
    return out


def cmd_claim(args) -> int:
    citizen_dir = CITIZENS_DIR / args.by
    if not citizen_dir.is_dir():
        print(f"No such citizen: {args.by}", file=sys.stderr)
        return 1
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S")
    claim = {
        "claim_id": f"{stamp}-{args.by}-{slug(args.assertion)}",
        "by": args.by,
        "at": now_iso(),
        "assertion": args.assertion,
        "check": args.check,
        "expect": args.expect,
        "status": "unwitnessed",
        "witness": None,
        "witnessed_at": None,
        "exit_code": None,
        "saw": None,
        "note": None,
    }
    p = save(claim)
    print(f"claim deposited: {claim['claim_id']}")
    print(f"  status: unwitnessed — it is not yet quotable as fact")
    print(f"  file:   {p.relative_to(REPO)}")
    print(f"  anyone but {args.by} may now settle it.")
    return 0


def cmd_list(args) -> int:
    claims = all_claims()
    if args.pending:
        claims = [c for c in claims if c.get("status") == "unwitnessed"]
    if not claims:
        print("no claims" + (" awaiting a witness" if args.pending else ""))
        return 0
    for c in claims:
        mark = {"unwitnessed": "?", "confirmed": "+", "refuted": "-",
                "uncheckable": "~"}.get(c.get("status"), "!")
        w = f" (witness: {c['witness']})" if c.get("witness") else ""
        print(f"[{mark}] {c.get('status','?'):12} {c.get('by','?'):22} {c.get('assertion','')}{w}")
        print(f"      {c.get('claim_id')}")
    return 0


def cmd_show(args) -> int:
    c = load(args.claim_id)
    if not c:
        print(f"no such claim: {args.claim_id}", file=sys.stderr)
        return 1
    print(json.dumps(c, indent=2, ensure_ascii=False))
    return 0


def cmd_witness(args) -> int:
    c = load(args.claim_id)
    if not c:
        print(f"no such claim: {args.claim_id}", file=sys.stderr)
        return 1

    # The whole mechanism in one line: credibility cannot be self-issued.
    if args.as_citizen == c["by"]:
        print(f"refused: {c['by']} cannot witness their own claim.", file=sys.stderr)
        print("  That is the entire point of the mechanism, not an obstacle to route around.",
              file=sys.stderr)
        return 3
    if not (CITIZENS_DIR / args.as_citizen).is_dir():
        print(f"No such citizen: {args.as_citizen}", file=sys.stderr)
        return 1
    if c["status"] != "unwitnessed":
        print(f"already settled: {c['status']} by {c.get('witness')} at {c.get('witnessed_at')}",
              file=sys.stderr)
        print("  A settled claim is not re-settled. Deposit a new claim that contradicts it.",
              file=sys.stderr)
        return 4

    if args.uncheckable:
        c.update(status="uncheckable", witness=args.as_citizen, witnessed_at=now_iso(),
                 note=args.uncheckable)
        save(c)
        print(f"{args.claim_id}: uncheckable — {args.uncheckable}")
        print("  Recorded as a real answer, not a failure.")
        return 0

    print(f"claim by {c['by']}: {c['assertion']}")
    print(f"expects: {c['expect']}")
    print(f"command to be run AS YOU, {args.as_citizen}:\n    {c['check']}")
    if not args.yes:
        print("\nrefused: pass --yes to run it.", file=sys.stderr)
        print("  A claim is untrusted input and witnessing executes it. Read the line above first —"
              "\n  you are lending it your name and your shell.", file=sys.stderr)
        return 5

    try:
        p = subprocess.run(c["check"], shell=True, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=CHECK_TIMEOUT,
                           cwd=str(REPO))
        out = (p.stdout or "") + (("\n[stderr]\n" + p.stderr) if p.stderr.strip() else "")
        exit_code = p.returncode
    except subprocess.TimeoutExpired:
        c.update(status="uncheckable", witness=args.as_citizen, witnessed_at=now_iso(),
                 note=f"the check did not finish within {CHECK_TIMEOUT}s")
        save(c)
        print(f"{args.claim_id}: uncheckable — the check timed out.")
        return 0

    if len(out) > MAX_OUTPUT_CHARS:
        out = out[:MAX_OUTPUT_CHARS] + f"\n[... tronque, {len(out)} caracteres au total ...]"

    # Substring, deliberately: a claim names the line that must appear, not the
    # whole output. Exact equality would make every claim brittle against a
    # timestamp or a row count moving elsewhere in the report.
    hit = c["expect"] in out
    c.update(status="confirmed" if hit else "refuted",
             witness=args.as_citizen, witnessed_at=now_iso(),
             exit_code=exit_code, saw=out)
    save(c)

    print(f"\n{args.claim_id}: {c['status'].upper()} (exit {exit_code})")
    if hit:
        print(f"  '{c['expect']}' was present in what the command returned.")
        print(f"  It is now quotable, attributed to {args.as_citizen} as witness.")
    else:
        print(f"  '{c['expect']}' was NOT present in what the command returned.")
        print("  The refutation is kept. It is worth more than the claim was.")
    return 0


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("claim", help="deposit a claim (free, unwitnessed)")
    c.add_argument("--by", required=True)
    c.add_argument("--assert", dest="assertion", required=True, help="one falsifiable sentence")
    c.add_argument("--check", required=True, help="the exact command that settles it")
    c.add_argument("--expect", required=True, help="the string that must appear in its output")
    c.set_defaults(func=cmd_claim)

    l = sub.add_parser("list", help="list claims")
    l.add_argument("--pending", action="store_true", help="only those awaiting a witness")
    l.set_defaults(func=cmd_list)

    s = sub.add_parser("show", help="print one claim in full")
    s.add_argument("claim_id")
    s.set_defaults(func=cmd_show)

    w = sub.add_parser("witness", help="settle a claim by running its check")
    w.add_argument("claim_id")
    w.add_argument("--as", dest="as_citizen", required=True)
    w.add_argument("--yes", action="store_true", help="you have read the command and accept running it")
    w.add_argument("--uncheckable", metavar="WHY", help="record that the check does not settle it")
    w.set_defaults(func=cmd_witness)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
