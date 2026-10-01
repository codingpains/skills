#!/usr/bin/env bash
# Set up a megalith worktree for wx-system work. This is the whole of the
# profile's § Worktree setup as one command, so the Lead runs it as its single
# background setup call (SKILL.md § 0 step 7) instead of assembling the steps.
#
#   megalith-wx-system.setup.sh <main checkout> <worktree> [--ui] [--check <workspace>]...
#
#   --ui                 also build wx-ui's API clients and compiled translations
#   --check <workspace>  type-check a workspace at the end (services/service-todo).
#                        Repeatable. A TS2307 there means the copied node_modules
#                        is behind its lockfile: install once and check again.
#
# Prints "setup: <step>" as it goes and ends with "setup: ok", or
# "setup: failed at <step>" and a non-zero exit. Safe to re-run.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
usage="usage: megalith-wx-system.setup.sh <main checkout> <worktree> [--ui] [--check <workspace>]..."
MAIN="${1:?$usage}"
WT="${2:?$usage}"
shift 2
UI=0
CHECKS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --ui) UI=1 ;;
    --check) CHECKS+=("${2:?--check needs a workspace}"); shift ;;
    *) echo "$usage" >&2; exit 2 ;;
  esac
  shift
done
MAIN="$(cd "$MAIN" && pwd)"
WT="$(cd "$WT" && pwd)"
WX="$WT/apps/wx-system"
LOG_DIR="$(mktemp -d)"

STEP=start
trap 'echo "setup: failed at $STEP"' ERR
step() { STEP="$1"; echo "setup: $1"; }

step node
set +u
# shellcheck disable=SC1090
source ~/.nvm/nvm.sh >/dev/null
nvm use "$(cat "$WX/.nvmrc")" >/dev/null
set -u
[ "$(node -v)" = "v$(cat "$WX/.nvmrc")" ] || { echo "setup: node is $(node -v), want v$(cat "$WX/.nvmrc")"; false; }

step "copy .env and node_modules from the main checkout"
bash "$HERE/../scripts/bootstrap-worktree.sh" "$MAIN" "$WT"

step "git hooks"
# lefthook lives in the repo-root node_modules; without it every hook silently does nothing.
[ -x "$WT/node_modules/lefthook-darwin-arm64/bin/lefthook" ] \
  || { echo "setup: no lefthook in $WT/node_modules: copy it with cp -c -R $MAIN/node_modules $WT/node_modules"; false; }

INSTALLED=0
install() {
  step "npm ci in apps/wx-system ($1)"
  (cd "$WX" && npm ci --no-audit --loglevel=error)
  INSTALLED=1
}
if cmp -s "$MAIN/apps/wx-system/package-lock.json" "$WX/package-lock.json"; then
  echo "setup: apps/wx-system lockfile matches the main checkout"
else
  install "lockfile differs from the main checkout"
fi

step "rebuild @fountain/cdc-contracts from this worktree"
# Installed as a copy, so it comes from the main checkout's branch; a newer base fails with TS2305.
(cd "$WT/packages/cdc-contracts" && npm run build --silent)
rsync -a --delete "$WT/packages/cdc-contracts/dist/" "$WX/node_modules/@fountain/cdc-contracts/dist/"

if [ "$UI" -eq 1 ]; then
  step "wx-ui API clients (clients:prebuild)"
  (cd "$WX" && npm run clients:prebuild --silent > "$LOG_DIR/clients.log" 2>&1) \
    || { tail -n 30 "$LOG_DIR/clients.log"; false; }
  step "wx-ui compiled translations"
  (cd "$WX" && npm run i18n:compile:local -w frontends/wx-ui --silent >/dev/null \
    && npm run formatjs:compile:src -w frontends/wx-ui --silent >/dev/null)
fi

for ws in ${CHECKS[@]+"${CHECKS[@]}"}; do
  step "type-check $ws"
  log="$LOG_DIR/tsc-${ws//\//-}.log"
  if ! (cd "$WX" && npx tsc -b "$ws" > "$log" 2>&1); then
    if [ "$INSTALLED" -eq 0 ] && grep -q 'TS2307' "$log"; then
      # A package the lockfile installs is missing: the main checkout was pulled but not reinstalled.
      grep -m 3 'TS2307' "$log"
      install "TS2307 in $ws"
      step "type-check $ws again"
      (cd "$WX" && npx tsc -b "$ws" > "$log" 2>&1) || { head -n 20 "$log"; false; }
    else
      head -n 20 "$log"
      false
    fi
  fi
done

STEP=done
echo "setup: ok"
