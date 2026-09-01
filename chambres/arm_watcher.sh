#!/bin/bash
# arm_watcher.sh — a citizen posts a lookout who will wake them again later.
#
# *Venice*: before leaving your desk you pay a boy a coin to come back and
# knock in a minute's time, and you tell him what to shout through the door.
# You are not staying awake; you are arranging to be woken.
#
# Substrate: spawns a detached `sleep <delay>; wake_citizen <self> "<question>"`
# which outlives the `claude -p` session that armed it (verified: a nohup'd
# child fired 20s after its launching shell had exited). The citizen's session
# ends normally; the watcher fires afterwards and starts a NEW session in the
# same folder, resuming via --continue.
#
# Usage, from inside your own citizens/<you>/ folder:
#   bash ../arm_watcher.sh 60 "The question you want to be asked on waking."
#   bash ../arm_watcher.sh --stop      # cancel a pending watcher, reset counter
#   bash ../arm_watcher.sh --status    # is one armed, and which generation
#
# THE COUNCIL'S RULE APPLIES TO YOURSELF. Never wake without a question — least
# of all yourself. "A citizen woken to be greeted writes a reflection and falls
# quiet. That is expenditure, not government." The question is mandatory and
# this script refuses to arm without one.
#
# THREE GUARDS, because a watcher that re-arms itself is an unbounded loop that
# spends real money while nobody is watching:
#   1. .watcher_stop       — if present when the watcher fires, it exits without
#                            waking anyone. The kill switch.
#   2. .watcher_generation — counts consecutive self-wakes; refuses to arm past
#                            WATCHER_MAX (default 20). Reset by --stop.
#   3. .watcher_armed      — one pending watcher at a time; replacing a live one
#                            requires --force.

set -uo pipefail

CITIZENS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ME="$(basename "$PWD")"
MY_DIR="$CITIZENS_DIR/$ME"
WATCHER_MAX="${WATCHER_MAX:-20}"

STOP_FILE="$MY_DIR/.watcher_stop"
GEN_FILE="$MY_DIR/.watcher_generation"
ARMED_FILE="$MY_DIR/.watcher_armed"

# Must be run from a citizen's own folder — the identity comes from the cwd,
# so running it anywhere else would arm a watcher for the wrong person.
if [ ! -d "$MY_DIR" ] || [ "$(cd .. && pwd)" != "$CITIZENS_DIR" ]; then
  echo "arm_watcher: run this from inside your own citizens/<you>/ folder (cwd is $PWD)" >&2
  exit 2
fi

FORCE=0
case "${1:-}" in
  --stop)
    : > "$STOP_FILE"
    rm -f "$ARMED_FILE" "$GEN_FILE"
    echo "watcher stopped for $ME; generation counter reset"
    exit 0
    ;;
  --status)
    if [ -f "$ARMED_FILE" ]; then
      echo "armed: $(cat "$ARMED_FILE")"
    else
      echo "no watcher armed for $ME"
    fi
    echo "generation: $(cat "$GEN_FILE" 2>/dev/null || echo 0) of $WATCHER_MAX"
    [ -f "$STOP_FILE" ] && echo "STOP FILE PRESENT — next watcher will decline to wake you"
    exit 0
    ;;
  --force) FORCE=1; shift ;;
esac

DELAY="${1:-}"
QUESTION="${2:-}"

if ! [[ "$DELAY" =~ ^[0-9]+$ ]] || [ "$DELAY" -lt 10 ]; then
  echo "arm_watcher: first argument must be a delay in seconds, at least 10" >&2
  exit 2
fi

if [ -z "$QUESTION" ]; then
  echo "arm_watcher: refusing to arm without a question." >&2
  echo "  Never wake without a question — least of all yourself." >&2
  exit 2
fi

GEN="$(cat "$GEN_FILE" 2>/dev/null || echo 0)"
[[ "$GEN" =~ ^[0-9]+$ ]] || GEN=0
if [ "$GEN" -ge "$WATCHER_MAX" ]; then
  echo "arm_watcher: generation $GEN has reached WATCHER_MAX=$WATCHER_MAX — refusing to arm." >&2
  echo "  This is the runaway guard. If the work genuinely needs more rounds, write" >&2
  echo "  why in your outbox/ and let a human raise the ceiling. Do not route around it." >&2
  exit 3
fi

if [ -f "$ARMED_FILE" ] && [ "$FORCE" -eq 0 ]; then
  echo "arm_watcher: a watcher is already armed ($(cat "$ARMED_FILE")). Use --force to replace it." >&2
  exit 4
fi

# Arming clears a previous stop: the citizen is explicitly asking to be woken.
rm -f "$STOP_FILE"
NEXT_GEN=$((GEN + 1))
echo "$NEXT_GEN" > "$GEN_FILE"
FIRE_AT="$(date -u -d "+${DELAY} seconds" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "+${DELAY}s")"
echo "generation $NEXT_GEN of $WATCHER_MAX, fires at $FIRE_AT (in ${DELAY}s)" > "$ARMED_FILE"

# Arguments are passed into the detached shell rather than interpolated, so a
# question containing quotes cannot break out and become code.
nohup bash -c '
  delay="$1"; my_dir="$2"; citizens_dir="$3"; me="$4"; question="$5"; gen="$6"
  sleep "$delay"
  rm -f "$my_dir/.watcher_armed"
  stamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if [ -f "$my_dir/.watcher_stop" ]; then
    echo "[$stamp] gen $gen declined to wake $me: stop file present" >> "$my_dir/.watcher.log"
    exit 0
  fi
  echo "[$stamp] gen $gen waking $me" >> "$my_dir/.watcher.log"
  # shellcheck source=/dev/null
  source "$citizens_dir/wake_citizen.sh"
  WAKER="your own watcher, generation $gen" wake_citizen "$me" "$question" \
    >> "$my_dir/.watcher.log" 2>&1
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] gen $gen session returned (exit $?)" >> "$my_dir/.watcher.log"
' _ "$DELAY" "$MY_DIR" "$CITIZENS_DIR" "$ME" "$QUESTION" "$NEXT_GEN" >/dev/null 2>&1 &

disown 2>/dev/null || true

echo "watcher armed for $ME: generation $NEXT_GEN of $WATCHER_MAX, fires in ${DELAY}s ($FIRE_AT)"
echo "cancel with: bash ../arm_watcher.sh --stop"
echo "log: citizens/$ME/.watcher.log"
