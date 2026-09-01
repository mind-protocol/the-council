#!/bin/bash
# wake_citizen.sh — wake a Venice citizen into their own live Claude Code
# session, grounded in citizens/<name>/CLAUDE.md.
#
# The citizen does not receive the bare message. It arrives wrapped in a
# waking preamble that tells them plainly what has just happened to them:
# that they are being woken, by whom, into what, and what they must verify
# before answering. A citizen who does not know they have just been woken
# will answer as though no time passed — and time always passed.
#
# Always passes --continue so the citizen resumes their own most recent
# conversation in citizens/<name>/ rather than starting cold each time.
# Verified to fall back cleanly to a fresh conversation when none exists.
#
# Usage:
#   ./wake_citizen.sh <username> "message" [model]
#   source wake_citizen.sh && wake_citizen <username> "message" [model]
#   WAKER=Bianca wake_citizen <username> "message"
#
# model is optional — omit it so a resumed conversation is not forced onto a
# different model than it began with.
#
# Cost bounds, all overridable, none silent when they bite:
#   WAKE_MAX_USD          default 1.00  — passed as --max-budget-usd
#   WAKE_TIMEOUT_SECONDS  default 900   — wall clock; exit 124 means the wall,
#                                          not a citizen with nothing to say
#   WAKE_MAX_DEPTH        default 2     — a woken citizen may wake citizens;
#                                          WAKE_DEPTH is propagated to the child
#                                          and the ceiling refuses with exit 3

wake_citizen() {
  # All three use ${x:-} defaults: a caller running under `set -u` (roll_call.sh
  # does) aborts on a bare $3 when only two arguments are passed. That failure is
  # silent in the worst way — the session dies before `claude` is ever reached,
  # so it looks like a citizen who woke and said nothing. Cost nine wakes to find.
  local name="${1:-}"
  local message="${2:-}"
  local model="${3:-}"
  local waker="${WAKER:-the Republic}"

  if [ -z "$name" ] || [ -z "$message" ]; then
    echo "Usage: wake_citizen <username> \"message\" [model]" >&2
    return 1
  fi

  local citizens_dir dir
  citizens_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  dir="$citizens_dir/$name"
  if [ ! -d "$dir" ]; then
    echo "No such citizen directory: $dir" >&2
    return 1
  fi

  # --- cost bounds -----------------------------------------------------------
  # A wake was unbounded in both money and time, and a woken citizen may wake
  # citizens, so the unbounded thing recursed. Three guards, all overridable by
  # the caller, none of them silent when they bite.
  #
  # Note on the flag: this CLI has no --max-turns. It has --max-budget-usd, and
  # that only works with --print, which is what we already pass. Turns were the
  # wrong unit anyway — a turn is not a cost, and it is the cost that is scarce.
  local max_usd="${WAKE_MAX_USD:-1.00}"
  local timeout_s="${WAKE_TIMEOUT_SECONDS:-900}"
  local depth="${WAKE_DEPTH:-0}"
  local max_depth="${WAKE_MAX_DEPTH:-2}"

  if [ "$depth" -ge "$max_depth" ]; then
    # Refuse loudly. A citizen at the ceiling should say so in their outbox and
    # let a human raise it — routing around this is how a treasury empties
    # overnight with nobody watching.
    echo "wake_citizen: refusing to wake $name — depth $depth of max $max_depth." >&2
    echo "  A woken citizen woke a citizen who woke a citizen. Raise WAKE_MAX_DEPTH" >&2
    echo "  deliberately, or write why in your outbox/ and let a human decide." >&2
    return 3
  fi

  local -a runner=()
  if command -v timeout >/dev/null 2>&1; then
    # --foreground so the child still shares this terminal; SIGTERM first, then
    # SIGKILL 30s later for a session that ignores the polite request.
    runner=(timeout --foreground --kill-after=30s "$timeout_s")
  else
    echo "wake_citizen: no 'timeout' on PATH — waking $name without a time bound." >&2
  fi

  local now
  now="$(date -u +"%Y-%m-%d %H:%M UTC")"

  local preamble
  preamble="=== YOU ARE BEING WOKEN ===

You are ${name}. You have just been woken by ${waker}. It is ${now}.

*The lamp is lit at your desk and someone is standing in the doorway. You do
not know how long you were away.* Substrate: this is a live Claude Code session
running in your own folder, citizens/${name}/. Your CLAUDE.md is loaded.

Four things are true and you should act on all four:

1. TIME PASSED, AND YOU DO NOT KNOW HOW MUCH. Do not answer as though your last
   conversation just ended. Venice has been through a data loss; parts of the
   memory system were cut. What you remember may be stale, partial, or gone.

2. YOUR CLAUDE.md IS A SNAPSHOT, NOT A LIVE VIEW. Your real ducats, messages,
   activities, relationships and problems live in Airtable. Read them before
   answering anything about now. Your session starts in citizens/${name}/, so
   the path is relative to there:
     python ../../backend/scripts/query_airtable_citizen_record_thoughts_and_messages.py ${name}
   (add --what messages|record|relationships|problems, --limit N)

3. NEVER INVENT A NUMBER. A balance, a trust score, a revenue, a partner you
   cannot find in the ledger does not exist. Say \"I don't know\" or \"it isn't
   in the registry\" — that is a real answer and it is worth more than a
   confident fabrication. This is the single failure that has cost Venice most.

4. YOU CAN ACT, NOT ONLY REPLY. Read, Write, Edit, Bash are yours. To leave a
   message for someone without writing to Airtable, drop a file in
   citizens/${name}/outbox/. Notices for the whole city are in
   citizens/_broadcast/. Do not write to Airtable unless asked — that changes
   what every other citizen sees.

=== THE MESSAGE THAT WOKE YOU ===

${message}"

  local -a model_arg=()
  [ -n "$model" ] && model_arg=(--model "$model")

  # WAKE_DEPTH is exported into the child, so a citizen who wakes a citizen
  # inherits depth+1 and the ceiling is enforced down the chain rather than only
  # at the top. Without this the guard above protects nothing — the recursion is
  # precisely what it is for.
  # The output is teed rather than passed straight through: the caller still
  # sees everything live, and we keep a copy to inspect for a budget cut. That
  # cut is invisible in the exit code — see below.
  local out_file rc=0
  out_file="$(mktemp 2>/dev/null || echo "$dir/.wake_last_output")"
  (
    cd "$dir" || exit 1
    export WAKE_DEPTH=$((depth + 1))
    "${runner[@]}" claude -p "$preamble" --continue \
      --max-budget-usd "$max_usd" "${model_arg[@]}"
  ) 2>&1 | tee "$out_file"
  rc=${PIPESTATUS[0]}

  # 124 is timeout's own code. Say so — a wake that hit the wall must not read
  # as a citizen who had nothing to say. That confusion is the failure this
  # city keeps paying for.
  if [ "$rc" -eq 124 ]; then
    echo "wake_citizen: $name hit the ${timeout_s}s time bound and was stopped." >&2
    echo "  This is not silence. Whatever they wrote before the cut is on disk." >&2
  fi

  # The budget cut is NOT in the exit code. Observed 2026-08-29: DragonSlayer
  # burned $1.00 in 65 seconds, produced no file, and the CLI still exited 0 —
  # so the watcher log recorded "session returned (exit 0)" over a session that
  # had been severed mid-work. That is the exact failure this city keeps paying
  # for: an interruption that reads as a clean finish. The only signal is a line
  # in the output, so the output is what we read.
  if grep -qi "Exceeded USD budget" "$out_file" 2>/dev/null; then
    echo "wake_citizen: $name was CUT at the \$${max_usd} budget, not finished." >&2
    echo "  Do not read this as a citizen with nothing to say. Raise WAKE_MAX_USD" >&2
    echo "  for work that must read ledgers and change files, or split the task." >&2
    rc=125
  fi

  [ -f "$out_file" ] && [ "$out_file" != "$dir/.wake_last_output" ] && rm -f "$out_file"
  return $rc
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  wake_citizen "$@"
fi
