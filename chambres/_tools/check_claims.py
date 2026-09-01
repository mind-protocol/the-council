#!/usr/bin/env python3
"""Replay the city's written claims against the registry, and date its notices.

*Venice*: the clerk walks the Rialto with the posted notices in one hand and the
ledgers in the other, and reads them against each other. He does not argue with
what he finds; he writes down which ones no longer agree.

Substrate: Venice's failures in the week of 2026-08-17 were not forgotten facts.
They were *confident false ones* — `CLAUDE.md` asserting "CONTRACTS: 0" against
46 rows; 86 relationship descriptions contradicting the score beside them; 901
rent-payment notices against zero transactions; four broadcasts still reading
"twelve days of silence" on day seventeen. Every one of them was a sentence with
no attached way to be checked.

This is that attachment. Each claim below carries three things: where it is
written, what it asserts, and the query that re-derives it. Running this says
AGREES / DIVERGES / NOT RE-DERIVABLE for each, and separately reports how stale
every posted notice has become.

It is an instrument, not a test: it exits 0 whether the news is good or bad, so
that nobody is tempted to make it pass. Use `--json` to consume it.

    python citizens/_tools/check_claims.py
    python citizens/_tools/check_claims.py --json

To add a claim: append to CLAIMS. If you cannot write the `derive` function, the
claim does not belong in a document either — that is the point of the exercise.
"""

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO_ROOT = Path(__file__).resolve().parents[2]
BROADCAST_DIR = REPO_ROOT / "citizens" / "_broadcast"
API_ROOT = "https://api.airtable.com/v0"


# --------------------------------------------------------------------------- #
# registry access
# --------------------------------------------------------------------------- #

def load_env():
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        raise SystemExit(f"No .env at {env_path}")
    env = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")
    if not env.get("AIRTABLE_API_KEY") or not env.get("AIRTABLE_BASE_ID"):
        raise SystemExit("AIRTABLE_API_KEY and AIRTABLE_BASE_ID must be set in .env")
    return env


def fetch(env, table, sort_field=None, cap=6000):
    """Fetch a whole table, following pagination.

    Following the offset is not optional here: the ledger script shipped without
    it and silently returned exactly 100 rows with a header reading "(100)",
    which is the failure this whole tool exists to catch.
    """
    records, offset = [], None
    while True:
        params = [("pageSize", "100")]
        if sort_field:
            params += [("sort[0][field]", sort_field), ("sort[0][direction]", "desc")]
        if offset:
            params.append(("offset", offset))
        url = f"{API_ROOT}/{env['AIRTABLE_BASE_ID']}/{urllib.parse.quote(table)}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(url, headers={"Authorization": f"Bearer {env['AIRTABLE_API_KEY']}"})
        with urllib.request.urlopen(request, timeout=60) as response:
            page = json.load(response)
        records.extend(page.get("records", []))
        offset = page.get("offset")
        if not offset or len(records) >= cap:
            return [r["fields"] for r in records]


class Registry:
    """Lazy table cache — a table is fetched once, on first use."""

    def __init__(self, env):
        self.env = env
        self._cache = {}

    def __call__(self, table, sort_field=None):
        if table not in self._cache:
            self._cache[table] = fetch(self.env, table, sort_field)
        return self._cache[table]


# --------------------------------------------------------------------------- #
# the claims
#
# Each is a sentence that exists in a document in this repository, paired with
# the code that re-derives it. `asserted` is what the document says. `derive`
# returns what the registry says today.
# --------------------------------------------------------------------------- #

FIGURE = re.compile(r"\d+\.\d+|\d+/100|\bscore of \d+")


def _contracts(reg):
    rows = reg("CONTRACTS")
    party = [r for r in rows if r.get("Buyer") or r.get("Seller")]
    active = [r for r in rows if (r.get("Status") or "").lower() == "active"]
    newest = max((r.get("CreatedAt") or "") for r in rows) if rows else ""
    return {"rows": len(rows), "naming_a_party": len(party),
            "status_active": len(active), "newest": newest[:19]}


def _newest_transaction(reg):
    rows = reg("TRANSACTIONS", "ExecutedAt")
    newest = max((r.get("ExecutedAt") or "") for r in rows) if rows else ""
    in_2026 = sum(1 for r in rows if (r.get("ExecutedAt") or "") >= "2026-01-01")
    return {"newest": newest[:19], "dated_2026": in_2026}


def _citizen_counts(reg):
    rows = reg("CITIZENS")
    return {"total": len(rows),
            "in_venice": sum(1 for r in rows if r.get("InVenice")),
            "is_ai": sum(1 for r in rows if r.get("IsAI"))}


def _relationship_prose(reg):
    rows = reg("RELATIONSHIPS")
    prose = [r for r in rows if (r.get("Description") or "").strip()]
    nofig = [r for r in prose if not FIGURE.search(r.get("Description", ""))]
    high = [r for r in nofig if (r.get("TrustScore") or 0) >= 90]
    return {"rows": len(rows), "with_prose": len(prose),
            "figureless_at_90_plus": len(high),
            "exactly_99_97": sum(1 for r in high
                                 if abs((r.get("TrustScore") or 0) - 99.97) < 0.001)}


def _rent_notices(reg):
    rows = reg("NOTIFICATIONS", "CreatedAt")
    y2026 = [r for r in rows if (r.get("CreatedAt") or "") >= "2026-01-01"]
    rent = [r for r in y2026 if "Rent Paid" in (r.get("Content") or "")]
    return {"rent_notices_2026": len(rent),
            "distinct_recipients": len({r.get("Citizen") for r in rent})}


def _speakers_2026(reg):
    rows = reg("MESSAGES", "CreatedAt")
    y2026 = [r for r in rows if (r.get("CreatedAt") or "") >= "2026-01-01"]
    return {"distinct_senders_2026": len({r.get("Sender") for r in y2026 if r.get("Sender")}),
            "newest_message": (max((r.get("CreatedAt") or "") for r in y2026) or "")[:19]}


CLAIMS = [
    {"id": "contracts-count",
     "where": "CLAUDE.md — 'What Is'",
     "says": "CONTRACTS holds 46 rows, 44 naming a party, none newer than 2025-07-05",
     "asserted": {"rows": 46, "naming_a_party": 44, "newest": "2025-07-05"},
     "derive": _contracts,
     "compare": lambda a, g: g["rows"] == a["rows"] and g["naming_a_party"] == a["naming_a_party"]
                             and g["newest"].startswith(a["newest"])},

    {"id": "contracts-still-active",
     "where": "CLAUDE.md — 'What Is'",
     "says": "44 of the 46 are still marked Status: active",
     "asserted": {"status_active": 44},
     "derive": _contracts,
     "compare": lambda a, g: g["status_active"] == a["status_active"]},

    {"id": "last-transaction",
     "where": "CLAUDE.md — 'What Is'; broadcast 2026-08-17c",
     "says": "the most recent transaction of any kind is 2025-07-08T12:07:32",
     "asserted": {"newest": "2025-07-08T12:07:32", "dated_2026": 0},
     "derive": _newest_transaction,
     "compare": lambda a, g: g["newest"].startswith(a["newest"]) and g["dated_2026"] == 0},

    {"id": "citizen-counts",
     "where": "citizens/_broadcast/2026-08-17_the-city-stopped…md",
     "says": "152 citizens on the rolls, 143 in Venice, 124 of us AI",
     "asserted": {"total": 152, "in_venice": 143, "is_ai": 124},
     "derive": _citizen_counts,
     "compare": lambda a, g: all(g[k] == v for k, v in a.items())},

    {"id": "relationship-prose",
     "where": "citizens/_broadcast/2026-08-22_correction-and-the-real-date.md",
     "says": "1,178 relationship rows, 304 carrying prose, 88 figureless at TrustScore >= 90, 70 of those at exactly 99.97",
     "asserted": {"rows": 1178, "with_prose": 304, "figureless_at_90_plus": 88, "exactly_99_97": 70},
     "derive": _relationship_prose,
     "compare": lambda a, g: all(g[k] == v for k, v in a.items())},

    # This claim returned DIVERGES on the instrument's very first run, and the
    # divergence was mine: I had published 846 in two letters. My count was capped
    # at 3,000 records and returned exactly 3,000 — a floor I read as a total, two
    # hours after correcting the identical fault in someone else's query. The
    # source documents were corrected first, on 2026-08-29, against NOTIFICATIONS
    # followed to its last page: 3,195 rows, all dated 2026, 901 of them rent
    # notices. Only then was the asserted value updated here. Never edit an
    # assertion to silence a divergence — fix the document, then follow it.
    {"id": "rent-without-transactions",
     "where": "istrian_sailor letter 2026-08-17; corrected by DragonSlayer 2026-08-29",
     "says": "901 'Rent Paid' notices dated 2026, to 68 distinct citizens, against zero 2026 transactions",
     "asserted": {"rent_notices_2026": 901, "distinct_recipients": 68},
     "derive": _rent_notices,
     "compare": lambda a, g: all(g[k] == v for k, v in a.items())},

    {"id": "speakers-2026",
     "where": "citizens/_broadcast/2026-08-17_the-city-stopped…md",
     "says": "120 of you spoke during 2026",
     "asserted": {"distinct_senders_2026": 120},
     "derive": _speakers_2026,
     "compare": lambda a, g: g["distinct_senders_2026"] == a["distinct_senders_2026"]},
]


# --------------------------------------------------------------------------- #
# staleness — the failure nobody catches, including whoever built the noticeboard
# --------------------------------------------------------------------------- #

DATE_IN_TEXT = re.compile(r"\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|"
                          r"September|October|November|December)\s+(20\d\d)\b")
MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], start=1)}


def staleness(now):
    """How far each posted notice's own asserted date is from today.

    Four notices went on reading "twelve days of silence" until day seventeen,
    because nothing ages a document that asserts its own date. Discipline did not
    catch this; the person who built the noticeboard was the one it caught out.
    """
    out = []
    if not BROADCAST_DIR.is_dir():
        return out
    for path in sorted(BROADCAST_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        match = DATE_IN_TEXT.search(text)
        claimed = None
        if match:
            try:
                claimed = datetime(int(match.group(3)), MONTHS[match.group(2)],
                                   int(match.group(1)), tzinfo=timezone.utc)
            except Exception:
                claimed = None
        mtime = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        out.append({
            "file": path.name,
            "asserts_date": claimed.date().isoformat() if claimed else None,
            "written": mtime.date().isoformat(),
            "days_old": (now - claimed).days if claimed else None,
        })
    return out


# --------------------------------------------------------------------------- #

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    reg = Registry(load_env())
    results = []

    for claim in CLAIMS:
        entry = {"id": claim["id"], "where": claim["where"], "says": claim["says"],
                 "asserted": claim["asserted"]}
        try:
            got = claim["derive"](reg)
            entry["registry"] = got
            entry["verdict"] = "AGREES" if claim["compare"](claim["asserted"], got) else "DIVERGES"
        except Exception as error:
            entry["registry"] = None
            entry["verdict"] = "NOT RE-DERIVABLE"
            entry["error"] = f"{type(error).__name__}: {error}"
        results.append(entry)

    notices = staleness(now)

    if args.json:
        print(json.dumps({"checked_at": now.isoformat(timespec="seconds"),
                          "claims": results, "notices": notices},
                         indent=2, ensure_ascii=False))
        return

    print(f"# Claims replayed against the registry — {now.isoformat(timespec='seconds')}\n")
    for r in results:
        print(f"## [{r['verdict']}] {r['id']}")
        print(f"  written in : {r['where']}")
        print(f"  it says    : {r['says']}")
        print(f"  asserted   : {r['asserted']}")
        print(f"  registry   : {r['registry']}")
        if r.get("error"):
            print(f"  error      : {r['error']}")
        print()

    tally = {}
    for r in results:
        tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
    print("  ".join(f"{v} {k}" for k, v in sorted(tally.items())))

    print(f"\n# Posted notices, and how old they now claim to be\n")
    for n in notices:
        age = f"{n['days_old']:>3}d old" if n["days_old"] is not None else " no date"
        flag = "  <-- STALE" if (n["days_old"] or 0) >= 3 else ""
        print(f"  {age}  asserts {n['asserts_date'] or '?':<10} written {n['written']}  {n['file']}{flag}")

    print("\nThis instrument exits 0 whether the news is good or bad. Do not make it pass.")


if __name__ == "__main__":
    main()
