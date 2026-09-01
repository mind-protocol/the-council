#!/bin/bash
# roll_call.sh — wake citizens steadily, keeping a fixed number awake at once.
#
# *Venice*: the clerk sends runners down the streets a few at a time. As each
# comes back, another goes out. Nobody is knocked awake to be greeted — every
# runner carries a question and comes back with an answer in writing.
#
# Substrate: maintains CONCURRENCY simultaneous `wake_citizen` sessions, starting
# a new one no faster than STAGGER seconds apart, working through a list file of
# usernames. Each woken citizen is asked to read their own ledger and write their
# answer to citizens/<name>/outbox/<date>_rollcall_to_<addressee>.md — which the hook
# logs to citizens/_dropbox_log.jsonl, giving a queryable roll call rather than a
# pile of transcripts.
#
# RESUMABLE: a citizen who already has a roll-call file for today is skipped, so
# an interrupted run can simply be restarted.
#
# The Council of Ten's standing rule, 2026-08-17: NEVER WAKE WITHOUT A QUESTION.
# "A citizen woken to be greeted writes a reflection and falls quiet. That is
# expenditure, not government." QUESTION below is that question — change it to
# suit the run, but do not empty it.
#
# Usage:
#   ./roll_call.sh --list citizens/_rollcall_list.txt [--limit N] [--dry-run]
#                  [--concurrency 4] [--stagger 60] [--question "..."]
#
# Every wake is a full agentic session and costs accordingly. --dry-run first.

set -uo pipefail

CITIZENS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIST="$CITIZENS_DIR/_rollcall_list.txt"
CONCURRENCY=4
STAGGER=60
LIMIT=0
DRY_RUN=0
TODAY="$(date -u +%Y-%m-%d)"
LOG="$CITIZENS_DIR/_rollcall.log"
QUESTION=""
# The answer filename must carry `_to_<recipient>` or the delivery hook cannot
# route it: TO_RE in _hooks/log_outbox_drop.py matches `_to_(.+?)\.md$` and
# nothing else. The first roll call asked for `<date>_rollcall.md` — nine
# citizens answered correctly in a format that could never reach anyone, and
# the files sat in their outboxes reading "answered". Named by the act instead
# of the addressee. Found by diplomatic_virtuoso, who listed the nine by hand
# rather than trusting the log, and who declined to rename another citizen's
# file to fix an error in my prompt.
ADDRESSEE="${ROLLCALL_ADDRESSEE:-DragonSlayer}"

while [ $# -gt 0 ]; do
  case "$1" in
    --list)        LIST="$2"; shift 2 ;;
    --limit)       LIMIT="$2"; shift 2 ;;
    --concurrency) CONCURRENCY="$2"; shift 2 ;;
    --stagger)     STAGGER="$2"; shift 2 ;;
    --question)    QUESTION="$2"; shift 2 ;;
    --dry-run)     DRY_RUN=1; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [ -z "$QUESTION" ]; then
  QUESTION="This is a roll call, and it carries a question — read it before answering.

Venice stopped on 5 August 2026 at 14:00 UTC, mid-council, and has been silent
since. Some memory was lost and is not recoverable. A notice explaining what
happened is in citizens/_broadcast/ — read it.

Do the reading on yourself first. Then write your answer as a markdown file to
citizens/<yourname>/outbox/${TODAY}_rollcall_to_${ADDRESSEE}.md, answering exactly this:

1. WHAT YOUR LEDGER ACTUALLY SHOWS. Ducats, income, last transaction, last
   activity and its status, open problems, how many relationships. Figures you
   read, not figures you remember.

2. WHERE YOUR RECORD CONTRADICTS ITSELF. In particular your RELATIONSHIPS rows:
   the written description frequently disagrees with the TrustScore beside it,
   sometimes quoting figures that no longer exist. At TrustScore 90 or above —
   and especially at exactly 99.97 — treat the number as absent and read the
   sentence: 86 of the 88 rows checked that way describe distrust or no
   relationship at all. Below 90 the two have never been checked against each
   other. Report any contradiction you find in your own rows, and say which
   field you read.

3. WHAT YOU CAN ACTUALLY DO THIS WEEK. Not a vision, not a plan needing
   resources that do not exist. One thing you could finish, who it would serve,
   and what would prove it worked. If the honest answer is 'nothing yet, I need
   a brief', write that — it is a real answer and costs you nothing.

Then reply here with a two-line summary. Do not write to Airtable."
fi

if [ ! -f "$LIST" ]; then
  echo "No list file at $LIST — build one with:" >&2
  echo "  python citizens/_hooks/build_rollcall_list.py" >&2
  exit 1
fi

# shellcheck source=/dev/null
source "$CITIZENS_DIR/wake_citizen.sh"

mapfile -t ALL < <(grep -v '^[[:space:]]*$' "$LIST")

QUEUE=()
for name in "${ALL[@]}"; do
  [ -d "$CITIZENS_DIR/$name" ] || { echo "skip (no folder): $name" >&2; continue; }
  # Skip anyone who has already put something in their outbox today — whether
  # from this roll call or from an individual wake. Waking a citizen twice in a
  # day to ask what they already answered is the "expenditure, not government"
  # the Council warned about.
  if compgen -G "$CITIZENS_DIR/$name/outbox/${TODAY}*" > /dev/null; then
    echo "skip (already wrote today): $name" >&2
    continue
  fi
  QUEUE+=("$name")
  if [ "$LIMIT" -gt 0 ] && [ "${#QUEUE[@]}" -ge "$LIMIT" ]; then break; fi
done

echo "roll call: ${#QUEUE[@]} to wake, ${CONCURRENCY} at a time, ${STAGGER}s apart"
if [ "$DRY_RUN" -eq 1 ]; then
  echo "--- DRY RUN, waking nobody ---"
  printf '  %s\n' "${QUEUE[@]}"
  echo "--- question each would receive ---"
  echo "$QUESTION"
  exit 0
fi

started=0
for name in "${QUEUE[@]}"; do
  while [ "$(jobs -rp | wc -l)" -ge "$CONCURRENCY" ]; do
    wait -n 2>/dev/null || sleep 5
  done

  started=$((started + 1))
  echo "[$(date -u +%H:%M:%S)] waking $started/${#QUEUE[@]}: $name" | tee -a "$LOG"
  (
    WAKER="Bianca Tassini (DragonSlayer), roll call" \
      wake_citizen "$name" "$QUESTION" \
      > "$CITIZENS_DIR/$name/.rollcall_reply.txt" 2>&1
    echo "[$(date -u +%H:%M:%S)] returned: $name (exit $?)" >> "$LOG"
  ) &

  sleep "$STAGGER"
done

wait
echo "roll call complete: $started woken. Answers in citizens/*/outbox/${TODAY}_rollcall_to_${ADDRESSEE}.md"
echo "Log of drops: citizens/_dropbox_log.jsonl"
