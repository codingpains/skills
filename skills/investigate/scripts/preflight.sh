#!/usr/bin/env zsh
# Report which data sources this investigation can reach, without printing secrets.
#
#   zsh ~/.claude/skills/investigate/scripts/preflight.sh <project>
#
# Reads the project profile's preflight.conf,
# $INVESTIGATIONS_HOME/projects/<project>/preflight.conf (else under ~/.investigations),
# one check per line:  kind|label|target
#   mongo|US production|MONGODB_URI        target = name of the env var holding the URI
#   postgres|Hire replica|DATABASE_URL     target = name of the env var holding the URI
#   sentry|Sentry|fountain                 target = org slug; checks the CLI login
#   cmd|Staging cluster|<command>          target = a read-only command; ok when it exits 0
# Env vars come from ~/.zshrc. Every check runs in parallel with a short timeout.

source ~/.zshrc >/dev/null 2>&1
HOME_DIR="${INVESTIGATIONS_HOME:-$HOME/.investigations}"
[[ -n "$1" ]] || { echo "usage: preflight.sh <project>  (profiles: $(ls "$HOME_DIR/projects" 2>/dev/null | tr '\n' ' '))" >&2; exit 2; }
CONF="$HOME_DIR/projects/$1/preflight.conf"
[[ -f "$CONF" ]] || { echo "preflight: no $CONF; nothing to check"; exit 0; }

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# Run a command with a time limit; macOS has no timeout(1) by default.
with_limit() {
  local secs=$1; shift
  "$@" & local pid=$!
  ( sleep "$secs"; kill "$pid" 2>/dev/null ) & local guard=$!
  wait "$pid" 2>/dev/null; local rc=$?
  kill "$guard" 2>/dev/null
  return $rc
}

check_mongo() {
  local var=$1 uri="${(P)1}"
  [[ -n "$uri" ]] || { echo "not set ($var)"; return; }
  command -v mongosh >/dev/null || { echo "mongosh not installed"; return; }
  [[ "$uri" == *\?* ]] && uri="$uri&serverSelectionTimeoutMS=6000" || uri="$uri?serverSelectionTimeoutMS=6000"
  if with_limit 12 mongosh "$uri" --quiet --eval 'db.runCommand({ping:1}).ok' >/dev/null 2>&1; then
    echo "reachable ($var)"
  else
    echo "set but unreachable ($var): VPN off or access expired?"
  fi
}

check_postgres() {
  local var=$1 uri="${(P)1}"
  [[ -n "$uri" ]] || { echo "not set ($var)"; return; }
  command -v psql >/dev/null || { echo "psql not installed"; return; }
  if with_limit 12 env PGCONNECT_TIMEOUT=6 psql "$uri" -tAc 'select 1' >/dev/null 2>&1; then
    echo "reachable ($var)"
  else
    echo "set but unreachable ($var): VPN off or access expired?"
  fi
}

check_sentry() {
  command -v sentry >/dev/null || { echo "sentry CLI not installed"; return; }
  if with_limit 15 sentry auth status >/dev/null 2>&1; then
    echo "logged in (org $1)"
  else
    echo "not logged in: run 'sentry auth login' yourself"
  fi
}

check_cmd() {
  if with_limit 15 zsh -c "source ~/.zshrc >/dev/null 2>&1; $1" >/dev/null 2>&1; then
    echo "ok"
  else
    echo "failed: $1"
  fi
}

i=0
while IFS='|' read -r kind label target; do
  [[ -z "$kind" || "$kind" == \#* ]] && continue
  i=$((i + 1))
  out="$tmp/$(printf '%03d' $i)"
  case "$kind" in
    mongo) { echo "$label: $(check_mongo "$target")" > "$out" } & ;;
    postgres) { echo "$label: $(check_postgres "$target")" > "$out" } & ;;
    sentry) { echo "$label: $(check_sentry "$target")" > "$out" } & ;;
    cmd) { echo "$label: $(check_cmd "$target")" > "$out" } & ;;
    *) echo "$label: unknown check kind '$kind'" > "$out" ;;
  esac
done < "$CONF"
wait

cat "$tmp"/* 2>/dev/null
