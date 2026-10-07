#!/usr/bin/env bash
# Set up a weride-ui worktree. This is the whole of the profile's § Worktree
# setup as one command, so the Lead runs it as its single background setup
# call (SKILL.md § 0 step 7).
#
#   weride-ui.setup.sh <main checkout> <worktree> [--spec <swagger.yaml>]
#
#   --spec  the weride-api contract to generate and check against. Default:
#           weride-api's origin/main. A full-stack ticket passes its weride-api
#           worktree's swagger/v1/swagger.yaml.
#
# packages/api-client/spec-path.ts finds the contract at <repo>/../weride-api,
# which from weride-ui-worktrees/<ticket> does not exist: generate:api then
# fails, and the lefthook openapi hook and generated-parity.test.ts skip
# without a word. This puts the contract at a fixed path inside the worktree
# (node_modules/.cache, gitignored), for WERIDE_API_SPEC.
#
# Prints "setup: <step>" as it goes and ends with "setup: ok", or
# "setup: failed at <step>" and a non-zero exit. Safe to re-run.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
usage="usage: weride-ui.setup.sh <main checkout> <worktree> [--spec <swagger.yaml>]"
MAIN="$(cd "${1:?$usage}" && pwd)"
WT="$(cd "${2:?$usage}" && pwd)"
shift 2
SPEC_SRC=""
while [ $# -gt 0 ]; do
  case "$1" in
    --spec) SPEC_SRC="$(cd "$(dirname "${2:?--spec needs a path}")" && pwd)/$(basename "$2")"; shift ;;
    *) echo "$usage" >&2; exit 2 ;;
  esac
  shift
done
API_MAIN="$(dirname "$MAIN")/weride-api"
SPEC="$WT/node_modules/.cache/weride-api/swagger.yaml"

STEP=start
trap 'echo "setup: failed at $STEP"' ERR
step() { STEP="$1"; echo "setup: $1"; }

step node
want="$(tr -d 'v \n' < "$WT/.nvmrc")"
have="$(node -v | sed 's/^v//')"
case "$have" in "$want"|"$want".*) ;; *) echo "setup: node is v$have, want v$want (.nvmrc)"; false ;; esac

step "copy node_modules from the main checkout"
log="$(mktemp)"
bash "$HERE/../scripts/bootstrap-worktree.sh" "$MAIN" "$WT" | tee "$log" | grep -v '^bootstrap: .*node_modules/$' || true
if grep -q 'run install' "$log"; then
  step "npm ci (lockfile differs from the main checkout)"
  (cd "$WT" && npm ci --no-audit --loglevel=error)
fi

step "weride-api contract"
mkdir -p "$(dirname "$SPEC")"
if [ -n "$SPEC_SRC" ]; then
  [ -f "$SPEC_SRC" ] || { echo "setup: no spec at $SPEC_SRC"; false; }
  ln -sf "$SPEC_SRC" "$SPEC"
  echo "setup: contract -> $SPEC_SRC"
else
  git -C "$API_MAIN" fetch --quiet origin main
  git -C "$API_MAIN" show origin/main:swagger/v1/swagger.yaml > "$SPEC"
  echo "setup: contract = weride-api origin/main $(git -C "$API_MAIN" rev-parse --short origin/main)"
fi

step "generated client parity"
# Informational: a client behind the contract is a fact for the Architect,
# not a setup failure. A ticket that needs a newer operation regenerates.
if (cd "$WT" && WERIDE_API_SPEC="$SPEC" npm run test -w packages/api-client -- src/generated-parity.test.ts > "$log" 2>&1); then
  echo "setup: parity ok: src/generated matches the contract"
else
  echo "setup: parity FAILS: src/generated is behind the contract; a ticket that needs a missing operation runs generate:api first (profile § Conditional checks)"
fi

STEP=done
echo "setup: ok (WERIDE_API_SPEC=$SPEC)"
