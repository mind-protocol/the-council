#!/usr/bin/env python3
"""Make a citizen *speak* — cheaply, and without letting them invent a number.

Two tiers exist for reaching a citizen, and they are not the same act:

  ACT   `wake_citizen.sh` — a full agentic session with tools. The citizen can
        read ledgers, write files, build things. Bounded at $1.00 by default.
        Use it when the citizen must DO something.

  SPEAK this tool — one `claude -p` call, Sonnet, **no tools at all**, bounded
        at $0.10. The citizen answers a question and nothing else.

The reason the cheap tier is dangerous, and the reason this file exists:

  A citizen with no tools CANNOT read their own ledger. Asked what they own,
  they will answer from `citizens/<name>/CLAUDE.md` — a snapshot — or from
  nothing at all, fluently, and be wrong. That is the single failure that has
  cost Venice most, and naively "making citizens cheaper" would industrialise
  it: 152 confident fabrications for the price of one honest session.

So the facts are fetched BEFORE the call, by this tool, from Airtable, and
injected into the prompt as the only numbers that exist. The citizen is told,
in the system prompt, that anything not in that block is unknown to them and
must be answered "je ne sais pas". Grounding is not a request made of the
model; it is a property of what the model was given.

The answer is then written to `citizens/<name>/outbox/<stamp>_to_<recipient>.md`
by this tool — not by the citizen, who has no Write tool. That filename is what
makes it MAIL rather than a diary entry: the delivery hook matches `_to_`, and
nine roll-call answers sit undelivered on this disk for want of it.

Usage:
    python citizens/speak_citizen.py <citizen> "<question>" --to <recipient>
    python citizens/speak_citizen.py DragonSlayer "..." --to mechanical_visionary --dry-run

Bounds (env, overridable):
    SPEAK_MAX_USD          default 0.10
    SPEAK_TIMEOUT_SECONDS  default 180
    SPEAK_MODEL            default sonnet
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CITIZENS_DIR = Path(__file__).resolve().parent
REPO = CITIZENS_DIR.parent
LEDGER = REPO / "backend" / "scripts" / "query_airtable_citizen_record_thoughts_and_messages.py"

# Enough to answer honestly, small enough that the prompt stays cheap. The
# whole point of this tier is that it costs cents; pulling ten tables would
# spend the saving back on tokens.
LEDGER_SLICES = ("record", "relationships")
LEDGER_LIMIT = "3"
MAX_FACTS_CHARS = 6000

# Never put these in a prompt. `citizens/CLAUDE.md` states that Wallet and the
# Telegram identifiers were deliberately kept out of the generated snapshots —
# but the ledger script prints them, so piping its output into a prompt quietly
# undoes that decision. Found by reading the tool's own output rather than by
# trusting that "it just fetches the record".
REDACT_FIELDS = {
    "Wallet", "TelegramUserId", "PartnerTelegramId", "PartnerTelegramUsername",
}

# Static prose already present in the citizen's own CLAUDE.md, which is loaded
# in the call anyway. Sending it twice is paying twice for the same paragraph:
# dropping it took the FACTS block from ~6,000 characters to a few hundred.
DROP_FIELDS = {
    "Description", "Personality", "ImagePrompt", "CoatOfArms", "CorePersonality",
    "FamilyMotto", "Color", "SecondaryColor", "VoiceId", "CitizenId",
}

SYSTEM_RULE = """You are answering as a citizen of Venice, in your own voice, from your own folder.

You have NO TOOLS in this call. You cannot read a ledger, run a script, or open a file.

Therefore: the FACTS block below is the entirety of what you know about your
current state. Any number, balance, relationship, debt, contract or event that
is not in that block does not exist for you right now. Say "je ne sais pas" or
"ce n'est pas dans ce qu'on m'a donne" — that is a complete and respectable
answer here, and it is worth more than a confident invention.

Your CLAUDE.md describes who you are. It is a SNAPSHOT and its numbers are
stale. When it disagrees with the FACTS block, the FACTS block wins.

Answer the question directly, in the language it was asked. Write as yourself,
not as an assistant. Do not open with a greeting or close with an offer of
further help."""


def filter_ledger(text: str) -> str:
    """Drop secrets and static prose from the ledger markdown.

    The ledger emits `- **Field**: value`, with prose values continuing on
    following lines until the next field. So a field is dropped together with
    its continuation, not just its first line — dropping only the first line
    would leave an orphan paragraph attributed to whatever field came next,
    which is worse than leaking it: it would be misattributed.
    """
    out, skipping = [], False
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("- **") and "**:" in stripped:
            field = stripped[4:stripped.index("**:")]
            if field in REDACT_FIELDS:
                out.append(f"- **{field}**: [redacted — never sent to a model]")
                skipping = True
                continue
            skipping = field in DROP_FIELDS
            if skipping:
                continue
        elif stripped.startswith("#") or stripped.startswith("### `"):
            skipping = False
        elif skipping:
            continue
        if not skipping:
            out.append(line)
    return "\n".join(out)


def fetch_facts(citizen: str) -> tuple[str, str]:
    """Return (facts_text, status). Never raises — an empty ledger is a fact."""
    if not LEDGER.is_file():
        return "", f"ledger script not found at {LEDGER}"
    chunks = []
    for what in LEDGER_SLICES:
        try:
            p = subprocess.run(
                [sys.executable, str(LEDGER), citizen, "--what", what, "--limit", LEDGER_LIMIT],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=120, cwd=str(REPO),
            )
        except Exception as e:
            return "", f"ledger query failed ({what}): {e}"
        if p.returncode != 0:
            # Report it rather than proceeding with a blank where facts should
            # be. A silent empty FACTS block reads to the citizen as "you own
            # nothing", which is a different lie from "nobody could look".
            return "", f"ledger query exit {p.returncode} on --what {what}: {(p.stderr or '').strip()[:200]}"
        chunks.append(filter_ledger(p.stdout).strip())
    text = "\n\n".join(c for c in chunks if c)
    if len(text) > MAX_FACTS_CHARS:
        text = text[:MAX_FACTS_CHARS] + "\n\n[... tronque ...]"
    return text, "ok"


def build_prompt(asker: str, question: str, facts: str, facts_status: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if facts_status == "ok" and facts:
        facts_block = facts
        caveat = ""
    else:
        facts_block = "(aucun fait n'a pu etre lu)"
        # The citizen must know the difference between "I have nothing" and
        # "nobody could look". These are not the same answer.
        caveat = (f"\n\nATTENTION : la lecture du registre a echoue ({facts_status}). "
                  f"Tu ne sais donc rien de ton etat actuel. Dis-le. "
                  f"N'en deduis pas que tu ne possedes rien.")
    return (f"{SYSTEM_RULE}{caveat}\n\n"
            f"=== FACTS — lus dans Airtable le {now}, seuls chiffres qui existent pour toi ===\n\n"
            f"{facts_block}\n\n"
            f"=== QUESTION, posee par {asker} ===\n\n"
            f"{question}")


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ap = argparse.ArgumentParser(description="Cheap, grounded citizen reply.")
    ap.add_argument("citizen")
    ap.add_argument("question")
    ap.add_argument("--to", required=True, help="recipient; sets the outbox filename")
    ap.add_argument("--asker", default=os.environ.get("WAKER", "the Republic"))
    ap.add_argument("--dry-run", action="store_true", help="build the prompt, call nothing")
    args = ap.parse_args()

    folder = CITIZENS_DIR / args.citizen
    if not folder.is_dir():
        print(f"No such citizen: {folder}", file=sys.stderr)
        return 1

    facts, status = fetch_facts(args.citizen)
    prompt = build_prompt(args.asker, args.question, facts, status)

    if args.dry_run:
        print(f"--- facts status: {status} ({len(facts)} chars) ---")
        print(prompt)
        return 0

    max_usd = os.environ.get("SPEAK_MAX_USD", "0.10")
    timeout_s = int(os.environ.get("SPEAK_TIMEOUT_SECONDS", "180"))
    model = os.environ.get("SPEAK_MODEL", "sonnet")

    cmd = [
        "claude", "-p", prompt,
        "--model", model,
        "--max-budget-usd", max_usd,
        # No tools. This is what makes the tier cheap, and what makes the
        # pre-fetched FACTS block load-bearing rather than decorative.
        "--disallowedTools", "Bash", "Read", "Write", "Edit", "Glob", "Grep",
        "WebFetch", "WebSearch", "Task",
    ]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout_s, cwd=str(folder))
    except subprocess.TimeoutExpired:
        print(f"speak_citizen: {args.citizen} hit the {timeout_s}s bound. "
              f"This is not silence — nothing was written.", file=sys.stderr)
        return 124

    answer = (p.stdout or "").strip()
    if p.returncode != 0 or not answer:
        print(f"speak_citizen: no answer (exit {p.returncode}). stderr: "
              f"{(p.stderr or '').strip()[:300]}", file=sys.stderr)
        return p.returncode or 2

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M")
    outbox = folder / "outbox"
    outbox.mkdir(exist_ok=True)
    path = outbox / f"{stamp}_to_{args.to}.md"
    header = (f"*Reponse de {args.citizen} a une question de {args.asker}, "
              f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}.*\n\n"
              f"**Question :** {args.question}\n\n---\n\n")
    footer = ("\n\n---\n\n*Substrat : reponse produite par `speak_citizen.py` — un appel "
              f"`claude -p --model {model}` SANS AUCUN OUTIL, plafonne a ${max_usd}. Les chiffres "
              "disponibles au citoyen etaient pre-lus dans Airtable et injectes ; il ne pouvait "
              "consulter aucune autre source. Aucune ecriture Airtable.*\n")
    path.write_text(header + answer + footer, encoding="utf-8")

    print(f"wrote {path.relative_to(REPO)} ({len(answer)} chars, facts: {status})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
