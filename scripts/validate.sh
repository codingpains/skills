#!/usr/bin/env bash
# Check every skill and agent in this repo is well formed before it is installed or committed.
#
#   skills/<name>/SKILL.md  frontmatter has name == <name> and a description
#   agents/<name>.md        frontmatter has name == <name>, a description, and a known model
#   codex/agents/<name>.toml has matching name, description, GPT model, effort and sandbox
#   skills/team-lead/repos/<name>.md  repo profile with name == <name> and a host/owner/repo remote
#   installed Claude and Codex references to a skill in this repo point at a real file
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

toml_field() {
  sed -nE "s/^$2[[:space:]]*=[[:space:]]*\"([^\"]*)\".*/\1/p" "$1" | head -1
}

for file in "$REPO"/skills/*/SKILL.md; do
  [ -f "$file" ] || continue
  dir="$(basename "$(dirname "$file")")"
  name="$(field "$file" name)"
  [ "$name" = "$dir" ] || fail "skills/$dir/SKILL.md: name '$name' does not match folder '$dir'"
  [ -n "$(field "$file" description)" ] || fail "skills/$dir/SKILL.md: missing description"
done

for file in "$REPO"/codex/agents/*.toml; do
  [ -f "$file" ] || continue
  base="$(basename "$file" .toml)"
  name="$(toml_field "$file" name)"
  [ "$name" = "$base" ] || fail "codex/agents/$base.toml: name '$name' does not match file name"
  [ -n "$(toml_field "$file" description)" ] || fail "codex/agents/$base.toml: missing description"
  model="$(toml_field "$file" model)"
  case "$model" in
    gpt-*-astra) fail "codex/agents/$base.toml: Astra is escalation-only, not a default agent model" ;;
    gpt-5.6-sol|gpt-5.6-terra|gpt-5.6-luna|gpt-6.1-*) ;;
    *) fail "codex/agents/$base.toml: unknown model '$model'" ;;
  esac
  effort="$(toml_field "$file" model_reasoning_effort)"
  case "$effort" in low|medium|high|xhigh|max|ultra) ;; *) fail "codex/agents/$base.toml: unknown reasoning effort '$effort'" ;; esac
  sandbox="$(toml_field "$file" sandbox_mode)"
  case "$sandbox" in read-only|workspace-write) ;; *) fail "codex/agents/$base.toml: unknown sandbox '$sandbox'" ;; esac
  grep -qF "team-lead-playbooks/$base.md" "$file" || fail "codex/agents/$base.toml: does not load its shared playbook"
  [ -f "$REPO/agents/$base.md" ] || fail "codex/agents/$base.toml: shared playbook agents/$base.md does not exist"
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
  workspace="$(field "$file" workspace)"
  if [ -n "$workspace" ]; then
    [ -z "$remote" ] || fail "repos/$base.md: has both remote and workspace"
    repos="$(field "$file" repos | tr -d '[] ' | tr ',' ' ')"
    [ -n "$repos" ] || fail "repos/$base.md: workspace profile lists no repos"
    for repo in $repos; do
      [ -f "$REPO/skills/team-lead/repos/$repo.md" ] || fail "repos/$base.md: no profile repos/$repo.md"
    done
  else
    case "$remote" in
      */*/*) ;;
      *) fail "repos/$base.md: remote '$remote' is not host/owner/repo" ;;
    esac
  fi
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

while IFS= read -r ref; do
  rel="${ref#\~/.agents/skills/}"
  skill="${rel%%/*}"
  if [ -d "$REPO/skills/$skill" ]; then
    [ -e "$REPO/skills/$rel" ] || fail "broken Codex reference: $ref"
  fi
done < <(grep -rhoE '~/\.agents/skills/[A-Za-z0-9_-]+/[A-Za-z0-9_./-]*[A-Za-z0-9_-]' "$REPO/skills" "$REPO/codex" | sort -u)

if [ "$errors" -gt 0 ]; then
  echo "validate: $errors problem(s)" >&2
  exit 1
fi
echo "validate: ok"
