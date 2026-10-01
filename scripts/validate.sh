#!/usr/bin/env bash
# Check every skill and agent in this repo is well formed before it is installed or committed.
#
#   skills/<name>/SKILL.md  frontmatter has name == <name> and a description
#   agents/<name>.md        frontmatter has name == <name>, a description, and a known model
#   skills/team-lead/repos/<name>.md  repo profile with name == <name> and a host/owner/repo remote
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

for file in "$REPO"/skills/team-lead/repos/*.md; do
  [ -f "$file" ] || continue
  base="$(basename "$file" .md)"
  name="$(field "$file" name)"
  [ "$name" = "$base" ] || fail "repos/$base.md: name '$name' does not match file name"
  remote="$(field "$file" remote)"
  case "$remote" in
    */*/*) ;;
    *) fail "repos/$base.md: remote '$remote' is not host/owner/repo" ;;
  esac
done

# References like ~/.claude/skills/team-lead/references/x.md must exist when the skill lives here.
# A reference into a skill installed from elsewhere is only checked on this machine, as a warning:
# that skill can change under us (wx-review dropped its scripts/ folder on 2026-09-29).
while IFS= read -r ref; do
  rel="${ref#\~/.claude/skills/}"
  skill="${rel%%/*}"
  if [ -d "$REPO/skills/$skill" ]; then
    [ -e "$REPO/skills/$rel" ] || fail "broken reference: $ref"
  elif [ -d "$HOME/.claude/skills/$skill" ] && [ ! -e "$HOME/.claude/skills/$rel" ]; then
    echo "validate: warning: $ref does not exist in the installed $skill skill" >&2
  fi
done < <(grep -rhoE '~/\.claude/skills/[A-Za-z0-9_-]+/[A-Za-z0-9_./-]*[A-Za-z0-9_-]' "$REPO/skills" "$REPO/agents" | sort -u)

if [ "$errors" -gt 0 ]; then
  echo "validate: $errors problem(s)" >&2
  exit 1
fi
echo "validate: ok"
