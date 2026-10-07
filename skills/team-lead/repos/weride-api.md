---
name: weride-api
remote: github.com/codingpains/weride-api
updated: 2026-10-07
---

# weride-api

The WeRide backend: Rails 8 API-only, Ruby 4.0.5 (asdf), PostgreSQL in the
OrbStack docker container `my-postgres`, RSpec (`test/` is vestigial),
rswag + committee for the OpenAPI contract. **Every command runs from the
worktree root.** The checkout lives in the `weride-go` workspace (profile
`weride-go`), next to `weride-ui`, which consumes `swagger/v1/swagger.yaml`.

The merge gate is `.github/workflows/ci.yml`: `scan_ruby` (brakeman,
bundler-audit), `lint` (`bin/rubocop --parallel`), `test`
(`bin/rails db:test:prepare`, `bundle exec rspec`) and `contract`
(swaggerize, then `git diff --exit-code -- swagger/v1/swagger.yaml`). CI does
not run `bin/critic`; the repo's `CLAUDE.md` still makes an A rating a
must-fix. `bin/ci` runs minitest: ignore it.

The rules live in `CLAUDE.md` (§ Code style is what reviews enforce),
`app/policies/README.md` and `docs/` (`api_error_codes.md`, `audit_log.md`,
`feature_flags.md`, `google_maps.md`). There is no `.claude/` folder: do not
look for `.claude/rules`. `AGENTS.md` mirrors `CLAUDE.md`: a change to one is
a change to both.

## Worktree setup

One command, run as the Lead's single background setup call (SKILL.md § 0
step 7):

`bash ~/.claude/skills/team-lead/repos/weride-api.setup.sh <main checkout> <worktree>`

About 10 s. It stops at the first failure and, in order: checks Ruby against
`.ruby-version`; copies `.env` with `bootstrap-worktree.sh`; runs
`bundle check || bundle install`; starts OrbStack and `my-postgres` when they
are down and waits for `pg_isready`; writes `.env.test.local` (gitignored)
with a `DATABASE_URL` for the worktree's own database,
`weride_api_test_<worktree folder>`; checks the test environment resolves to
it; creates it and loads `db/schema.rb`; and runs two canary spec files.
The log ends in `setup: ok (<database>)`.

Why: `config/database.yml` gives every checkout the same `weride_api_test`,
and the main checkout's `.env` sets `DATABASE_URL` to
`weride_api_development`, so without this a worktree's specs and migrations
run against the human's dev database, parallel runs purge each other's
tables, and every spec after `spec/requests/blazer_access_spec.rb` fails with
`ConnectionNotEstablished` / `fe_sendauth: no password supplied`. Nine runs
lost 3–8 minutes each to that and called the failures pre-existing. After
setup the full suite is green (2602 examples, 40 s on 2026-10-07).

When the worktree is removed after merge, drop its database first:
`bash ~/.claude/skills/team-lead/repos/weride-api.setup.sh --drop <worktree>`.

Git hooks: lefthook is in the bundle but not installed in this clone
(`.git/hooks` holds only samples), so the pre-commit rubocop and swaggerize
never run. Do both by hand (§ Checks by change). Never run
`lefthook install`: hooks are shared by every worktree and the main
checkout.

## Checks by change

| Changed | Run | Notes |
|---|---|---|
| any `.rb` file | `bin/rubocop --force-exclusion <files>` | `--force-exclusion` keeps `db/schema.rb` out (258 offenses otherwise); CI runs `bin/rubocop --parallel` |
| `app/` or `lib/` `.rb` | `bin/critic --base <base sha>` | every touched file must rate A; it always analyses all of `app/` and `lib/` (2 s) and takes no file arguments. Pass the base SHA: the default `main` is the local branch, which lags `origin/main` and gates other people's merged files |
| source with specs | `bundle exec rspec <touched specs> <specs beside touched files>` | 4–13 s. `spec/commands/`, `spec/policies/`, `spec/requests/`, `spec/presenters/`, `spec/models/` mirror `app/` |
| a new or renamed constant, a new file under `app/` | `CI=1 RAILS_ENV=test bin/rails zeitwerk:check` | the test env eager-loads only with `CI` set (`config/environments/test.rb:16`), so a misnamed file passes rspec locally and fails in CI |
| a request spec, `spec/swagger_helper.rb`, a response shape, a route | `RAILS_ENV=test bundle exec rake rswag:specs:swaggerize`, then the touched request specs, then `git diff --stat <base> -- swagger/` | `rspec spec/requests` never writes `swagger.yaml`; only the rake task does (1–4 s). Commit the regenerated file. CI `contract` fails on drift |
| tests only | the test files; rubocop on them | specs are excluded from the critic gate |
| `Gemfile` / `Gemfile.lock` | `bundle install`, `bundle exec bundler-audit`, `bundle exec brakeman --no-pager -q` | |
| controllers, commands, auth, anything taking user input | `bundle exec brakeman --no-pager -q` | 0 warnings passes. Not `bin/brakeman`: it adds `--ensure-latest` and exits 5 whenever a newer brakeman exists (8.0.6 pinned, 8.1.0 out); that is not a finding |
| tenancy, auth, the partner-context resolver, rack-attack | `bundle exec rspec spec/services/tenancy spec/requests/tenant_scoping_spec.rb spec/requests/rack_attack_spec.rb`, and the full suite once per block | |
| a block of the plan is done, or the change spans many areas | `bundle exec rspec` (full, 40 s) | only meaningful after setup ended in `setup: ok`. A run with hundreds of failures after `blazer_access_spec` is a setup fault, never a pre-existing failure: stop and re-run setup |

## Conditional checks

| When this changes | Also run | Why |
|---|---|---|
| a migration | `RAILS_ENV=test bin/rails db:migrate` in the worktree; commit `db/schema.rb` | `maintain_test_schema!` aborts rspec on a pending migration. The `schema.rb` diff must hold only the version line and this migration's change: anything else came from another branch's database. Take a timestamp later than every migration on `origin/main` and in the other open worktrees (`ls ../*/db/migrate | sort | tail -3`) |
| a new command | add it to `CommandRegistry` (and `SENSITIVE_COMMAND_NAMES` when sensitive); `bundle exec rspec spec/commands/command_registry_spec.rb spec/openapi` | `spec/openapi/operation_ids_spec.rb` requires a unique camelCase `operationId` and one POST per `/api/commands/*` path. Every command needs a request spec, a command spec and a policy spec (`CLAUDE.md` § Testing conventions) |
| a new error `code` | a row in `docs/api_error_codes.md`; the code in the rswag `response` description | rswag keeps one description per status: the last `response "422"` block wins, so a second code under the same status vanishes from `swagger.yaml`. Check the regenerated file, not the spec source |
| an audited model or event | `docs/audit_log.md` | |
| a tenant-scoped model | the `"tenant-scoped resource"` shared example (`spec/support/shared_examples/tenant_scoping.rb`) | cross-tenant access must 404, never 403 |
| a Flipper flag | `docs/feature_flags.md`; a PR-body justification | specs use in-memory Flipper (`spec/support/flipper.rb`) unless tagged `:flipper_active_record` |
| `swagger/v1/swagger.yaml` | tell the Lead: the PR body says `weride-ui` must run `npm run generate:api` after merge | the contract is the only link to `weride-ui` (profile `weride-go`) |
| production config (`config/environments/production.rb`, the `production:` block of `config/database.yml`, a `config/*.yml` that reads `DATABASE_URL`) | read each production database and check it has the tables its feature needs (`rg -n solid_cache db/schema.rb db/*_schema.rb`); in a runner, load the config with a sample `DATABASE_URL` and print it | no spec covers production-only paths; WERIDE-23's one must-fix (Solid Cache on a database without its table) was found only this way |

## Rule greps

Findings reviews kept making. The Hardener runs them on the whole diff before
its first edit, the Tester on its own commits. Resolve every hit, or name it
under *Left alone on purpose* with the reason. `BASE` is the base commit.

- An error code the branch adds that the contract does not carry (4 runs).
  Run after swaggerize:
  `for c in $(git diff $BASE...HEAD -U0 -- app lib | rg -o '^\+.*"([A-Z][A-Z0-9_]{3,})"' -r '$1' | sort -u); do rg -q "\b$c\b" swagger/v1/swagger.yaml || echo "not in swagger.yaml: $c"; done`
- An absolute claim in an added comment, rswag description or example name
  (10 runs; `CLAUDE.md` § Comments: comments that drifted from the code).
  Check each against the code:
  `git diff $BASE...HEAD -U0 | rg '^\+.*(#|description|\bit ").*\b(always|never|every|only|any|all|exactly|guarantees|ensures)\b'`
- A vacuous assertion: a value compared with itself, or a
  `not_to change` around a block that only reads (4 runs; § Tests):
  `git diff $BASE...HEAD -U0 -- spec | rg -P '^\+.*(expect\((\w+)\)\.to eq\(\2\)|not_to\(?\s*change)'`
- A coercing attribute on a command input: `:integer` turns `true` into 1
  and `"12abc"` into 12 (WERIDE-51):
  `git diff $BASE...HEAD -U0 -- app/commands | rg '^\+\s*attribute :\w+, :(integer|float|decimal)'`

Ticket IDs in comments are this repo's own convention (`(WERIDE-130)` in
283 files): do not flag them.

## Quality tools

- Complexity and duplication: `bin/critic --base <base sha>` (RubyCritic:
  reek, flog, flay). A per file; it names the smells and lines behind a
  rating. It is the gate the repo itself sets; there is no other threshold.
- Coverage: the repo has none configured and no CI coverage job. Measure with
  the loader beside this profile:
  `COV_FILES=<comma-separated app/ or lib/ paths> COV_DIR=<tmp>/cov RUBYOPT=-r$HOME/.claude/skills/team-lead/repos/weride-api.coverage.rb bundle exec rspec <spec paths>`.
  It prints `<file>: lines N% (covered/total), branches c/t, missed lines [...]`
  for each file and writes the same lines to `$COV_DIR/summary.txt`. Run the
  specs that exercise the touched files, not the suite.
- Coverage of the base commit, for the touched-files-no-drop target: a
  second worktree with its own database, never one without (its
  `maintain_test_schema!` purges whatever database it reaches):
  `git -C <main checkout> worktree add --detach <tmp>/base <base sha>`,
  `bash ~/.claude/skills/team-lead/repos/weride-api.setup.sh <main checkout> <tmp>/base`,
  run the same loader command there, then
  `bash ~/.claude/skills/team-lead/repos/weride-api.setup.sh --drop <tmp>/base`
  and `git -C <main checkout> worktree remove --force <tmp>/base`. Setup takes
  about 10 s.

## Never

- `bin/rails db:prepare` on a new database: it seeds roles and permissions
  and about 470 specs fail.
- `db:test:prepare`, `db:schema:load`, `db:rollback`, `db:drop`,
  `db:environment:set`, or any `db:` task without `RAILS_ENV=test` in a
  worktree: without it they reach `weride_api_development`, the human's
  database. The setup script is the only thing that loads the schema.
- `rspec --exclude-pattern` or skipping `blazer_access_spec.rb` to get green:
  its failure means setup is broken.
- `bin/brakeman` as a pass/fail signal (above), `bin/ci` (minitest),
  rubocop on `db/schema.rb` without `--force-exclusion`.
- Swaggerize from the Reviewer, or any redirect into a tracked file
  (`> swagger/v1/swagger.yaml`): it rewrites the contract under review.
- `lefthook install` (above). `timeout` and GNU `sed -i` (macOS: `sed -i ''`).
- Reading `.env` or `.env.test.local`: they hold the database password.
  `bin/rails runner 'print ActiveRecord::Base.connection_db_config.database'`
  (with `RAILS_ENV=test`) says which database a command will reach.

## Gotchas

- `ActiveRecord::EnvironmentMismatchError ... last run in development`, or
  hundreds of failures from `blazer_access_spec.rb` on: the worktree is on a
  shared database. Re-run setup; it ends in `setup: ok (weride_api_test_<folder>)`.
- `connection refused` on 5432: OrbStack or `my-postgres` stopped. Re-run
  setup; it starts both. `pg_isready` and `psql` are not on the host: use
  `docker exec my-postgres pg_isready`.
- `bin/critic` gates 80–100 files: it diffed against the stale local `main`.
  Pass `--base <base sha>`.
- `spec/tasks/admin_bootstrap` fails at `--seed 4242`: pre-existing order
  dependence (2026-10-06). Do not re-prove it on the base.
- `RideEvent` is read-only once persisted: tests change it with `update_all`.
- `spec/examples.txt` shows up untracked after rspec runs: never commit it.
- Two tickets run from the same base collide on `swagger.yaml`, the
  `CLAUDE.md`/`AGENTS.md` tables and `docs/api_error_codes.md`. After the
  other merges: merge `origin/main`, re-run swaggerize and
  `RAILS_ENV=test bin/rails db:migrate`, commit what they change.
- `master.key` is not needed: specs stub credentials. CI passes
  `RAILS_MASTER_KEY` anyway.
- Commit subjects: `[WERIDE-NN] <type>: <subject>`, the convention in
  `git log origin/main` (profile `weride-go` § Conventions).
