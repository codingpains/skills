#!/usr/bin/env bash
# Set up a weride-api worktree: gems, Postgres, and a test database of its own.
# This is the whole of the profile's § Worktree setup as one command, so the
# Lead runs it as its single background setup call (SKILL.md § 0 step 7).
#
#   weride-api.setup.sh <main checkout> <worktree>
#   weride-api.setup.sh --drop <worktree>      drop the worktree's test database
#
# Why a database per worktree: config/database.yml names one test database
# (weride_api_test) for every checkout, and the main checkout's .env sets a
# DATABASE_URL that points test runs at weride_api_development. Parallel runs
# then purge each other's tables, migrations land in the human's dev database,
# and spec/requests/blazer_access_spec.rb (Blazer reads DATABASE_URL itself)
# breaks the connection for every spec after it. This script writes the
# worktree's own DATABASE_URL to .env.test.local (gitignored), which
# dotenv-rails loads before .env in the test environment only.
#
# Never prints a secret: .env is parsed by Ruby and only the database name is
# echoed. Prints "setup: <step>" as it goes and ends with "setup: ok", or
# "setup: failed at <step>" and a non-zero exit. Safe to re-run.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
usage="usage: weride-api.setup.sh <main checkout> <worktree> | --drop <worktree>"
CONTAINER=my-postgres

STEP=start
trap 'echo "setup: failed at $STEP"' ERR
step() { STEP="$1"; echo "setup: $1"; }

db_name() {
  local slug
  slug="$(basename "$1" | tr '[:upper:]-' '[:lower:]_' | tr -cd 'a-z0-9_')"
  echo "weride_api_test_${slug}"
}

postgres_up() {
  step "postgres ($CONTAINER)"
  if ! docker info >/dev/null 2>&1; then
    orb start >/dev/null 2>&1 || open -a OrbStack
    for _ in $(seq 1 60); do docker info >/dev/null 2>&1 && break; sleep 1; done
    docker info >/dev/null 2>&1 || { echo "setup: docker did not start (OrbStack)"; false; }
  fi
  [ "$(docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null)" = true ] \
    || docker start "$CONTAINER" >/dev/null
  for _ in $(seq 1 30); do docker exec "$CONTAINER" pg_isready -q && return 0; sleep 1; done
  echo "setup: $CONTAINER is not accepting connections"; false
}

if [ "${1:-}" = "--drop" ]; then
  WT="$(cd "${2:?$usage}" && pwd)"
  postgres_up
  step "drop $(db_name "$WT")"
  [ -f "$WT/.env.test.local" ] || { echo "setup: no .env.test.local in $WT; nothing to drop"; exit 0; }
  (cd "$WT" && RAILS_ENV=test bin/rails db:drop)
  STEP=done
  echo "setup: ok"
  exit 0
fi

MAIN="$(cd "${1:?$usage}" && pwd)"
WT="$(cd "${2:?$usage}" && pwd)"
[ "$MAIN" != "$WT" ] || { echo "setup: refusing to run on the main checkout"; exit 2; }
DB="$(db_name "$WT")"

step ruby
want="$(sed 's/^ruby-//' "$WT/.ruby-version")"
have="$(cd "$WT" && ruby -e 'print RUBY_VERSION')"
[ "$have" = "$want" ] || { echo "setup: ruby is $have, want $want (asdf install ruby $want)"; false; }

step "copy .env from the main checkout"
bash "$HERE/../scripts/bootstrap-worktree.sh" "$MAIN" "$WT"
[ -f "$WT/.env" ] || { echo "setup: no .env in $WT; DATABASE_USERNAME and DATABASE_PASSWORD come from it"; false; }

step gems
(cd "$WT" && { bundle check >/dev/null || bundle install --quiet; })

postgres_up

step "test database $DB (.env.test.local)"
# Credentials go into the URL because Blazer connects with DATABASE_URL as is,
# without database.yml's username and password.
(cd "$WT" && DB="$DB" bundle exec ruby -rdotenv -rerb -e '
  env = Dotenv.parse(".env")
  enc = ->(v) { ERB::Util.url_encode(v.to_s) }
  user = env["DATABASE_USERNAME"].to_s
  auth = user.empty? ? "" : "#{enc.(user)}:#{enc.(env["DATABASE_PASSWORD"])}@"
  host = env.fetch("DATABASE_HOST", "localhost")
  File.write(".env.test.local",
    "# Written by the team-lead weride-api setup: this worktree'\''s own test database.\n" \
    "DATABASE_URL=postgresql://#{auth}#{host}/#{ENV.fetch("DB")}\n")
  File.chmod(0o600, ".env.test.local")
')
git -C "$WT" check-ignore -q .env.test.local || { echo "setup: .env.test.local is not gitignored"; false; }

got="$(cd "$WT" && RAILS_ENV=test bin/rails runner 'print ActiveRecord::Base.connection_db_config.database' 2>/dev/null)"
[ "$got" = "$DB" ] || { echo "setup: test env resolves to '$got', want '$DB'"; false; }

step "load db/schema.rb into $DB"
# db:create is a no-op when it exists. Never db:prepare: on a new database it
# also seeds roles and permissions, and about 470 specs then fail.
(cd "$WT" && RAILS_ENV=test bin/rails db:create >/dev/null && RAILS_ENV=test bin/rails db:schema:load >/dev/null)

step "canary specs"
log="$(mktemp)"
if ! (cd "$WT" && bundle exec rspec spec/requests/blazer_access_spec.rb spec/requests/cors_spec.rb --order defined > "$log" 2>&1); then
  tail -n 30 "$log"; false
fi
grep -E '^[0-9]+ examples?, 0 failures' "$log"

STEP=done
echo "setup: ok ($DB)"
