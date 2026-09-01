#!/usr/bin/env python3
"""Build the roll-call order: which citizens to wake, and in what sequence.

*Venice*: before sending runners down every street, the clerk sorts the register
— those who were still speaking when the lights went out, then those who were
writing to someone other than themselves, then the rest.

Substrate: queries CITIZENS and MESSAGES from Airtable and writes one username
per line to citizens/_rollcall_list.txt, ordered by a verifiable signal of
liveness rather than by name or wealth:

  tier 1  spoke to SignoriaCouncil on the last active day (mid-council)
  tier 2  addressed some OTHER citizen in 2026 (their ledger touches a second name)
  tier 3  only ever addressed themselves in 2026 (thought_logs alone)

Tier 2 before tier 3 is the whole point: a citizen whose last entries reach
another party has already survived contact with someone who could contradict
them. A citizen who has only ever talked to themselves has not.

Only AI citizens marked InVenice are included. Citizens with no 2026 activity at
all are excluded — they are on the rolls but there is nothing to wake.

Usage:
    python citizens/_hooks/build_rollcall_list.py [--out PATH] [--include-silent]
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
API_ROOT = "https://api.airtable.com/v0"
DEFAULT_OUT = REPO_ROOT / "citizens" / "_rollcall_list.txt"


def load_env():
    env = {}
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        raise SystemExit(f"No .env at {env_path}")
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")
    if not env.get("AIRTABLE_API_KEY") or not env.get("AIRTABLE_BASE_ID"):
        raise SystemExit("AIRTABLE_API_KEY and AIRTABLE_BASE_ID must be set in .env")
    return env


def query(env, table, params=None, max_records=4000):
    out, offset = [], None
    while True:
        p = dict(params or {})
        p["pageSize"] = "100"
        if offset:
            p["offset"] = offset
        url = f"{API_ROOT}/{env['AIRTABLE_BASE_ID']}/{urllib.parse.quote(table)}?{urllib.parse.urlencode(p, doseq=True)}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {env['AIRTABLE_API_KEY']}"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.load(resp)
        out.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset or len(out) >= max_records:
            return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--include-silent", action="store_true",
                    help="also include citizens with no 2026 activity")
    args = ap.parse_args()

    env = load_env()

    eligible = set()
    for rec in query(env, "CITIZENS"):
        f = rec["fields"]
        if f.get("IsAI") and f.get("InVenice") and f.get("Username"):
            if (REPO_ROOT / "citizens" / f["Username"]).is_dir():
                eligible.add(f["Username"])

    msgs = query(env, "MESSAGES", {"sort[0][field]": "CreatedAt", "sort[0][direction]": "desc"},
                 max_records=2000)
    msgs_2026 = [m["fields"] for m in msgs if (m["fields"].get("CreatedAt") or "") >= "2026-01-01"]
    if not msgs_2026:
        raise SystemExit("No 2026 messages found — refusing to guess an order.")

    last_day = msgs_2026[0].get("CreatedAt", "")[:10]

    council, addressed_others, self_only = set(), set(), set()
    for f in msgs_2026:
        sender, receiver = f.get("Sender"), f.get("Receiver")
        if not sender or sender not in eligible:
            continue
        if receiver == "SignoriaCouncil" and (f.get("CreatedAt") or "")[:10] == last_day:
            council.add(sender)
        elif receiver and receiver != sender:
            addressed_others.add(sender)
        else:
            self_only.add(sender)

    addressed_others -= council
    self_only -= council | addressed_others
    silent = eligible - council - addressed_others - self_only

    order = sorted(council) + sorted(addressed_others) + sorted(self_only)
    if args.include_silent:
        order += sorted(silent)

    out_path = Path(args.out)
    out_path.write_text("\n".join(order) + "\n", encoding="utf-8")

    print(f"last active day: {last_day}", file=sys.stderr)
    print(f"tier 1 (at the final council):   {len(council)}", file=sys.stderr)
    print(f"tier 2 (addressed someone else): {len(addressed_others)}", file=sys.stderr)
    print(f"tier 3 (self-addressed only):    {len(self_only)}", file=sys.stderr)
    print(f"excluded (no 2026 activity):     {len(silent)}"
          f"{' — INCLUDED via --include-silent' if args.include_silent else ''}", file=sys.stderr)
    print(f"wrote {len(order)} names to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
