#!/usr/bin/env bash
# Wait, without spending tokens, until an open PR needs the Lead.
#
#   pr-watch.sh <PR URL> <watch dir> [--every SECONDS] [--for SECONDS]
#   pr-watch.sh --ack <watch dir>
#
# Every --every seconds (300) it scores the PR with pr-gates.py and writes
# <watch dir>/state.json. It exits as soon as the PR's state is news: not
# `running`, and a signature (state, head commit, waiting gates, item keys)
# different from <watch dir>/acted, which `--ack` writes once the Lead has
# acted on the current state. It exits too, even while a gate runs, when the
# PR is ready for a human review (`review_ready`) and <watch dir>/review-asked
# does not exist: the Lead writes it once it has asked. And it exits after
# --for seconds (6900, under Claude Code's 2-hour limit for a background
# command) so the Lead can re-arm it. The last line says why:
#
#   watch: news <overall> <head>     state.json holds the news
#   watch: timeout <overall> <head>  nothing new; run it again
#   watch: error <message>           three reads in a row failed
#
# Reads only; never writes to GitHub.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
usage="usage: pr-watch.sh <PR URL> <watch dir> [--every SECONDS] [--for SECONDS] | --ack <watch dir>"

field() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])' "$1" "$2"; }

if [ "${1:-}" = "--ack" ]; then
  dir="${2:?$usage}"
  field "$dir/state.json" signature > "$dir/acted"
  echo "watch: acked $(field "$dir/state.json" overall) $(field "$dir/state.json" head)"
  exit 0
fi

pr="${1:?$usage}"
dir="${2:?$usage}"
shift 2
every=300
duration=6900
while [ $# -gt 0 ]; do
  case "$1" in
    --every) every="$2"; shift 2 ;;
    --for) duration="$2"; shift 2 ;;
    *) echo "$usage" >&2; exit 64 ;;
  esac
done

mkdir -p "$dir"
touch "$dir/acted"
deadline=$(( $(date +%s) + duration ))
errors=0

while :; do
  if python3 "$HERE/pr-gates.py" "$pr" > "$dir/state.next" 2> "$dir/error.log"; then
    errors=0
    mv "$dir/state.next" "$dir/state.json"
    overall="$(field "$dir/state.json" overall)"
    head="$(field "$dir/state.json" head)"
    news=no
    if [ "$overall" != running ] && [ "$(field "$dir/state.json" signature)" != "$(cat "$dir/acted")" ]; then
      news=yes
    fi
    if [ "$(field "$dir/state.json" review_ready)" = True ] && [ ! -e "$dir/review-asked" ]; then
      news=yes
    fi
    if [ "$news" = yes ]; then
      python3 "$HERE/pr-gates.py" --show "$dir/state.json"
      echo "watch: news $overall $head"
      exit 0
    fi
  else
    errors=$((errors + 1))
    if [ "$errors" -ge 3 ]; then
      echo "watch: error $(tail -1 "$dir/error.log")"
      exit 3
    fi
  fi
  if [ $(( $(date +%s) + every )) -gt "$deadline" ]; then
    echo "watch: timeout ${overall:-unknown} ${head:-unknown}"
    exit 0
  fi
  sleep "$every"
done
