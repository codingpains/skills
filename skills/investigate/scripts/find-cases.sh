#!/usr/bin/env bash
# List past investigation cases that mention any of the given keys.
#
#   bash ~/.claude/skills/investigate/scripts/find-cases.sh '#61d172f8' WX-SYSTEM-47G 7feedb20 ONB-1406
#
# Keys are matched case-insensitively as plain text against every case file and
# evidence file in $INVESTIGATIONS_HOME (else ~/.investigations). Prints each
# matching case once, with the keys it matched and its index.jsonl line.
# Written for the bash 3.2 that ships with macOS: no associative arrays.
set -euo pipefail

HOME_DIR="${INVESTIGATIONS_HOME:-$HOME/.investigations}"
[ "$#" -gt 0 ] || { echo "usage: find-cases.sh <key>..." >&2; exit 2; }
[ -d "$HOME_DIR" ] || { echo "no cases yet ($HOME_DIR missing)"; exit 0; }

pairs="$(mktemp)"
trap 'rm -f "$pairs"' EXIT

for key in "$@"; do
  { grep -rilF -- "$key" "$HOME_DIR" --include='*.md' --include='*.txt' --include='*.json' 2>/dev/null || true; } |
    while IFS= read -r file; do
      rel="${file#"$HOME_DIR"/}"
      case="${rel%%/*}"
      # Skip top-level files and folders such as _imported-memory.
      case "$case" in _*) continue ;; esac
      [ "$case" = "$rel" ] && continue
      printf '%s\t%s\n' "$case" "$key"
    done >> "$pairs"
done

[ -s "$pairs" ] || { echo "no matching cases"; exit 0; }

sort -u "$pairs" | awk -F'\t' '{ k[$1] = ($1 in k) ? k[$1] ", " $2 : $2 } END { for (c in k) print c "\t" k[c] }' |
  sort | while IFS=$'\t' read -r case keys; do
    echo "== $case  (matched: $keys)"
    grep -F "\"case\":\"$case\"" "$HOME_DIR/index.jsonl" 2>/dev/null | head -1 || true
  done
