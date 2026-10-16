#!/usr/bin/env bash
# Check the team-lead repo profiles are well formed, after /team-lead
# --configure-repo writes one or after a hand edit.
#
#   check-profiles.sh [folder]     default ~/.team-lead/repos
#
#   <name>.md          repo profile with name == <name> and a host/owner/repo
#                      remote, or a workspace profile whose repos all exist
#   <repo>.gates.json  valid JSON with a host/owner/repo remote and known gate kinds
set -euo pipefail

DIR="${1:-$HOME/.team-lead/repos}"
errors=0
fail() { echo "check-profiles: $1" >&2; errors=$((errors + 1)); }

# Value of a top-level frontmatter key, quotes stripped.
field() {
  awk -v key="$2" '
    NR == 1 && $0 != "---" { exit }
    NR > 1 && $0 == "---" { exit }
    NR > 1 && index($0, key ":") == 1 {
      sub("^" key ":[ ]*", ""); gsub(/^["'\'']|["'\'']$/, ""); print; exit
    }' "$1"
}

[ -d "$DIR" ] || { echo "check-profiles: no folder $DIR (no profiles yet)"; exit 0; }

for file in "$DIR"/*.md; do
  [ -f "$file" ] || continue
  base="$(basename "$file" .md)"
  name="$(field "$file" name)"
  [ "$name" = "$base" ] || fail "$base.md: name '$name' does not match file name"
  remote="$(field "$file" remote)"
  workspace="$(field "$file" workspace)"
  if [ -n "$workspace" ]; then
    [ -z "$remote" ] || fail "$base.md: has both remote and workspace"
    repos="$(field "$file" repos | tr -d '[] ' | tr ',' ' ')"
    [ -n "$repos" ] || fail "$base.md: workspace profile lists no repos"
    for repo in $repos; do
      [ -f "$DIR/$repo.md" ] || fail "$base.md: no profile $repo.md"
    done
  else
    case "$remote" in
      */*/*) ;;
      *) fail "$base.md: remote '$remote' is not host/owner/repo" ;;
    esac
  fi
done

for file in "$DIR"/*.gates.json; do
  [ -f "$file" ] || continue
  problem="$(python3 - "$file" 2>&1 <<'PY'
import json, sys
try:
    data = json.load(open(sys.argv[1]))
except ValueError as error:
    sys.exit(f"not valid JSON: {error}")
if data.get("remote", "").count("/") != 2:
    sys.exit(f"remote '{data.get('remote')}' is not host/owner/repo")
kinds = {"checks", "human", "reef", "visual-qa"}
for gate in data.get("gates") or sys.exit("no gates"):
    if not gate.get("id") or gate.get("kind") not in kinds:
        sys.exit(f"gate {gate.get('id')!r} has unknown kind {gate.get('kind')!r}")
PY
)" || fail "$(basename "$file"): $problem"
done

if [ "$errors" -gt 0 ]; then
  echo "check-profiles: $errors problem(s)" >&2
  exit 1
fi
echo "check-profiles: ok ($DIR)"
