#!/usr/bin/env python3
"""Audit the BUILDINGS table for occupancy fields keyed inconsistently.

*The customs clerk's oldest trick: do not read what the manifest says, read what
kind of thing it says it in. A crate labelled by number among crates labelled by
name is not a crate you have counted.*

Substrate: BUILDINGS.Owner / RunBy / Occupant are expected to hold a citizen
`Username`. Some rows hold an Airtable record id (`rec` + 14 chars) instead.
Any comparison of the form `Owner == Occupant`, or any tenant census grouped by
`Occupant`, silently produces a wrong answer on those rows -- it does not error,
it just disagrees with reality. That is the failure mode worth catching: a
result indistinguishable from a correct one.

Run:
    python citizens/TopGlassmaker/tools/audit_building_occupancy_key_types.py
    python citizens/TopGlassmaker/tools/audit_building_occupancy_key_types.py --json

Exit code is 1 when any inconsistently-keyed row is found, 0 when clean, so it
can be wired into a check that fails loudly.

Written by Caterina Baffo (TopGlassmaker), 17 August 2026, after finding one
such row in her own property.
"""

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request

RECORD_ID = re.compile(r"^rec[A-Za-z0-9]{14}$")
KEYED_FIELDS = ("Owner", "RunBy", "Occupant")


def load_env(path):
    env = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def fetch_all(table, api_key, base_id):
    records, offset = [], None
    while True:
        params = {"pageSize": "100"}
        if offset:
            params["offset"] = offset
        url = "https://api.airtable.com/v0/{}/{}?{}".format(
            base_id, urllib.parse.quote(table), urllib.parse.urlencode(params)
        )
        request = urllib.request.Request(url, headers={"Authorization": "Bearer " + api_key})
        payload = json.load(urllib.request.urlopen(request))
        records.extend(payload.get("records", []))
        offset = payload.get("offset")
        if not offset:
            return records


def audit(buildings, citizens_by_id):
    findings = []
    counts = {}
    for record in buildings:
        fields = record.get("fields", {})
        for field in KEYED_FIELDS:
            value = fields.get(field)
            if value is None:
                kind = "empty"
            elif RECORD_ID.match(str(value)):
                kind = "record_id"
            else:
                kind = "username"
            counts["{}:{}".format(field, kind)] = counts.get("{}:{}".format(field, kind), 0) + 1
            if kind != "record_id":
                continue
            resolved = citizens_by_id.get(value)
            findings.append(
                {
                    "building": fields.get("Name"),
                    "buildingRecordId": record.get("id"),
                    "field": field,
                    "storedValue": value,
                    "resolvesTo": resolved,
                    "owner": fields.get("Owner"),
                    # The consequence, stated as the wrong answer it produces:
                    "ownerEqualsOccupantNaive": fields.get("Owner") == value,
                    "ownerEqualsOccupantTrue": fields.get("Owner") == resolved,
                }
            )
    return findings, counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit findings as JSON")
    args = parser.parse_args()

    env = load_env(os.path.join(repo_root(), ".env"))
    api_key = env["AIRTABLE_API_KEY"]
    base_id = env.get("AIRTABLE_BASE_ID", "appk6RszUo2a2L2L8")

    buildings = fetch_all("BUILDINGS", api_key, base_id)
    citizens = fetch_all("CITIZENS", api_key, base_id)
    citizens_by_id = {r["id"]: r.get("fields", {}).get("Username") for r in citizens}

    findings, counts = audit(buildings, citizens_by_id)

    if args.json:
        json.dump(
            {"buildingsScanned": len(buildings), "keyTypeCounts": counts, "findings": findings},
            sys.stdout,
            indent=2,
        )
        print()
        return 1 if findings else 0

    print("BUILDINGS scanned: {}".format(len(buildings)))
    print("\nKey type by field:")
    for key in sorted(counts):
        print("  {:<24} {}".format(key, counts[key]))

    if not findings:
        print("\nNo inconsistently-keyed rows. Every occupancy field holds a Username.")
        return 0

    print("\n{} row(s) hold a record id where a Username is expected:\n".format(len(findings)))
    for f in findings:
        print("  {} -- field {}".format(f["building"], f["field"]))
        print("    stored:      {}  (resolves to {})".format(f["storedValue"], f["resolvesTo"]))
        print("    Owner:       {}".format(f["owner"]))
        print(
            "    Owner==Occupant reads {} by the stored key, {} in fact".format(
                f["ownerEqualsOccupantNaive"], f["ownerEqualsOccupantTrue"]
            )
        )
        print()
    print(
        "Each row above answers an occupancy question wrongly without erroring.\n"
        "A tenant census grouped on Occupant invents one phantom citizen per row."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
