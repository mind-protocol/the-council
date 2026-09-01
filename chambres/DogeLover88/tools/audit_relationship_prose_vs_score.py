#!/usr/bin/env python3
"""Audit RELATIONSHIPS rows where the prose contradicts the numeric fields.

*Lorenzo checks the margin notes against the columns, row by row, the way he
checks a batch of glass against the mould before it leaves the furnace.*

Substrate: pages the whole RELATIONSHIPS table, pulls every number the
Description/Title claims about trust or strength, and compares each against the
TrustScore / StrengthScore field on the same record. Reads only. Writes nothing
back to Airtable.

Usage (from repo root):
    python citizens/DogeLover88/tools/audit_relationship_prose_vs_score.py
    python citizens/DogeLover88/tools/audit_relationship_prose_vs_score.py --citizen DogeLover88
    python citizens/DogeLover88/tools/audit_relationship_prose_vs_score.py --tolerance 5 --json
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "backend" / "scripts"))
from query_airtable_citizen_record_thoughts_and_messages import load_env  # noqa: E402

API_ROOT = "https://api.airtable.com/v0"

# "trust ... 61.26", "Trust Score of 0", "low-trust (25.4/100)", "32.1/100".
# The lookbehind matters: usernames carry digits (DogeLover88, BankingWizard99),
# and "Low Trust DogeLover88" otherwise reads as a trust claim of 88.
TRUST_CLAIM = re.compile(r"trust[^.;\n]{0,40}?(?<![\w.])(\d+(?:\.\d+)?)", re.IGNORECASE)
STRENGTH_CLAIM = re.compile(r"strength[^.;\n]{0,40}?(?<![\w.])(\d+(?:\.\d+)?)", re.IGNORECASE)


def fetch_all(env, table, formula=None):
    """Page every record of a table. Airtable caps a page at 100."""
    records, offset = [], None
    while True:
        params = [("pageSize", "100")]
        if formula:
            params.append(("filterByFormula", formula))
        if offset:
            params.append(("offset", offset))
        url = f"{API_ROOT}/{env['AIRTABLE_BASE_ID']}/{urllib.parse.quote(table)}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(url, headers={"Authorization": f"Bearer {env['AIRTABLE_API_KEY']}"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as error:
            raise SystemExit(f"Airtable {error.code} on {table}: {error.read().decode('utf-8', 'replace')}")
        records.extend(payload.get("records", []))
        offset = payload.get("offset")
        if not offset:
            return records


def claims(text, pattern):
    """Every number the prose asserts, deduplicated, order preserved."""
    seen, out = set(), []
    for raw in pattern.findall(text or ""):
        value = float(raw)
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def audit(records, tolerance):
    findings = []
    for record in records:
        fields = record.get("fields", {})
        prose = " ".join(filter(None, [fields.get("Title"), fields.get("Description")]))
        if not prose.strip():
            continue
        for label, field_name, pattern in (
            ("trust", "TrustScore", TRUST_CLAIM),
            ("strength", "StrengthScore", STRENGTH_CLAIM),
        ):
            actual = fields.get(field_name)
            if actual is None:
                continue
            for stated in claims(prose, pattern):
                if abs(stated - float(actual)) > tolerance:
                    findings.append(
                        {
                            "id": record["id"],
                            "citizen1": fields.get("Citizen1"),
                            "citizen2": fields.get("Citizen2"),
                            "field": field_name,
                            "actual": float(actual),
                            "stated_in_prose": stated,
                            "kind": label,
                        }
                    )
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--citizen", help="restrict to rows naming this username")
    parser.add_argument("--tolerance", type=float, default=2.0, help="allowed gap before it counts (default 2.0)")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    args = parser.parse_args()

    env = load_env()
    formula = None
    if args.citizen:
        name = args.citizen.replace("'", r"\'")
        formula = f"OR({{Citizen1}}='{name}',{{Citizen2}}='{name}')"

    records = fetch_all(env, "RELATIONSHIPS", formula)
    with_prose = sum(1 for r in records if (r.get("fields", {}).get("Description") or r.get("fields", {}).get("Title")))
    findings = audit(records, args.tolerance)

    if args.json:
        print(json.dumps({"scanned": len(records), "with_prose": with_prose, "findings": findings}, indent=2))
        return

    print(f"# RELATIONSHIPS audit — prose against columns\n")
    print(f"- rows scanned: **{len(records)}**")
    print(f"- rows carrying a Title or Description: **{with_prose}**")
    print(f"- contradictions (gap > {args.tolerance}): **{len(findings)}**\n")
    if not findings:
        print("_No contradiction found at this tolerance._")
        return
    print("| relationship | field | column says | prose says | gap |")
    print("| --- | --- | ---: | ---: | ---: |")
    for f in sorted(findings, key=lambda f: -abs(f["actual"] - f["stated_in_prose"])):
        gap = abs(f["actual"] - f["stated_in_prose"])
        print(f"| {f['citizen1']} ↔ {f['citizen2']} | {f['field']} | {f['actual']:g} | {f['stated_in_prose']:g} | {gap:.2f} |")


if __name__ == "__main__":
    main()
