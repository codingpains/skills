#!/usr/bin/env bash
# Check every skill and agent in this repo is well formed before it is installed or committed.
#
#   skills/<name>/SKILL.md  frontmatter has name == <name> and a description
#   agents/<name>.md        frontmatter has name == <name>, a description, and a known model
#   ~/.claude/skills/<skill>/<path> references to a skill in this repo point at a real file
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
errors=0
fail() { echo "validate: $1" >&2; errors=$((errors + 1)); }

# Value of a top-level frontmatter key, quotes stripped.
field() {
  awk -v key="$2" '
    NR == 1 && $0 != "---" { exit }
    NR > 1 && $0 == "---" { exit }
    NR > 1 && index($0, key ":") == 1 {
      sub("^" key ":[ ]*", ""); gsub(/^["'\'']|["'\'']$/, ""); print; exit
    }' "$1"
}

for file in "$REPO"/skills/*/SKILL.md; do
  [ -f "$file" ] || continue
  dir="$(basename "$(dirname "$file")")"
  name="$(field "$file" name)"
  [ "$name" = "$dir" ] || fail "skills/$dir/SKILL.md: name '$name' does not match folder '$dir'"
  [ -n "$(field "$file" description)" ] || fail "skills/$dir/SKILL.md: missing description"
done

for file in "$REPO"/agents/*.md; do
  [ -f "$file" ] || continue
  base="$(basename "$file" .md)"
  name="$(field "$file" name)"
  [ "$name" = "$base" ] || fail "agents/$base.md: name '$name' does not match file name"
  [ -n "$(field "$file" description)" ] || fail "agents/$base.md: missing description"
  model="$(field "$file" model)"
  case "$model" in
    ''|sonnet|opus|haiku|fable|inherit|claude-*) ;;
    *) fail "agents/$base.md: unknown model '$model'" ;;
  esac
done

# References like ~/.claude/skills/team-lead/references/x.md must exist when the skill lives here.
while IFS= read -r ref; do
  rel="${ref#\~/.claude/skills/}"
  skill="${rel%%/*}"
  [ -d "$REPO/skills/$skill" ] || continue
  [ -e "$REPO/skills/$rel" ] || fail "broken reference: $ref"
done < <(grep -rhoE '~/\.claude/skills/[A-Za-z0-9_-]+/[A-Za-z0-9_./-]*[A-Za-z0-9_-]' "$REPO/skills" "$REPO/agents" | sort -u)

if [ "$errors" -gt 0 ]; then
  echo "validate: $errors problem(s)" >&2
  exit 1
fi
echo "validate: ok"
