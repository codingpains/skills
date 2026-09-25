---
name: megalith-wx-system
remote: github.com/onboardiq/megalith
paths: [apps/wx-system/]
updated: 2026-09-24
---

# megalith / wx-system

The WX npm monorepo inside megalith. Workspaces: `frameworks/*`,
`services/*`, `tools/*`, `frontends/*` (`terraform/` has no packages). Node
24.15.0 with `engine-strict`. **Every command below runs from
`<worktree>/apps/wx-system`** unless it says otherwise. Paths passed to a
workspace's test script are relative to that workspace.

The merge gate is the repo-root `.rwx/wx-system-build-and-test.yml`. The
copies under `apps/wx-system/.rwx/` and `apps/wx-system/.github/workflows/`
are dead leftovers; ignore them.

## Worktree setup

1. `node -v` must print `v24.15.0`. If not: `source ~/.nvm/nvm.sh && nvm use`
   (from `apps/wx-system`, which has an `.nvmrc`).
2. From the worktree root:
   `WX_REVIEW_SOURCE_CLONE=<main checkout> bash ~/.claude/skills/wx-review/scripts/bootstrap-worktree.sh`.
   It copies every `.env` under `apps/wx-system`, and clones
   (copy-on-write) every `node_modules`, `dist`, `generated` (API clients)
   and `compiled` (translations) folder under `apps/wx-system` and
   `packages/`. When that script is missing, use the generic
   `~/.claude/skills/team-lead/scripts/bootstrap-worktree.sh`, then
   `npm run clients:prebuild` if wx-ui is touched.
3. If `apps/wx-system/package-lock.json` differs from the main checkout's
   (`cmp`), run `npm ci --no-audit` (minutes; one long timeout).
4. The copied `dist/` folders come from whatever branch the main checkout is
   on. Before running a workspace's tests, build it and what it depends on:
   `npx tsc -b <workspace>` (incremental, fast after the first run).

## Checks by change

| Changed | Run | Notes |
|---|---|---|
| any `.ts/.tsx/.js/.mjs/.cjs/.json/.yml` file | `npx oxfmt --check <files>` (fix: `npx oxfmt <files>`) | CI runs `oxfmt --check .`; Prettier is inactive |
| any `.ts/.tsx/.js` file | `npx oxlint --type-aware --max-warnings 0 <files>` | the commit hook lints **without** `--type-aware`, so type-aware errors only show in CI unless you run this |
| `services/<name>` or `frameworks/<name>` source | `npx tsc -b <workspace>`; then `npm test -w <workspace> -- <test paths>` for the touched tests and the tests beside touched files | always `npm test`, never `npx jest`/`npx vitest`: the script carries `--forceExit`, `--passWithNoTests` and log settings. Jest or Vitest depends on the workspace |
| `frameworks/<name>` source | also `npm run compile:backends`, and the tests of dependents that call the changed code (`rg "@fountain/<name>"`) | dependents import the framework's built `dist/` |
| `frontends/wx-ui` | `npm run typecheck -w frontends/wx-ui`; tests: `npm run test:file -w frontends/wx-ui -- run <paths>` | needs generated clients and compiled translations (setup step 2) |
| `tools/tool-ecosystem` | `npx tsc -b tools/tool-ecosystem`; `npm test -w tools/tool-ecosystem -- <paths>` | the other `tools/*` have no tests that CI runs |
| test files only | the test files as above; oxfmt and oxlint on them | framework tsconfigs exclude tests, so `tsc` never checks framework test files |
| a new `@fountain/<workspace>` import | `node scripts/check-tsconfig-refs.js` | fails when the tsconfig reference is missing |

## Conditional checks

| When this changes | Also run | Why |
|---|---|---|
| a route, schema, `*.openapi.ts` or anything under `routes/` that the frontend consumes | `npm run build:backends && npm run clients && npm run compile:frontends` | clients are gitignored (nothing to commit) but wx-ui must still compile against them |
| `frameworks/waterworks-backend-hire-internal`, `-hire-public-v2`, or `apps/hire/swagger/{internal_api,api/v2}/fountain.yaml` | `npm run codegen`, commit `frameworks/*/generated` | CI `hire-sdk-diff` fails on stale generated SDKs; never hand-edit them |
| a `*.template.yml` (permissions) | `npm run rebuild:authz`, commit what it changes (unverified) | `apps/wx-system/CLAUDE.md` § Commands |
| an i18n message in wx-ui | `npm run i18n:extract:source -w frontends/wx-ui`, commit only `src/i18n/translations/en-US.json`; then `npm run formatjs:compile -w frontends/wx-ui && npm run i18n:check -w frontends/wx-ui` | never commit other locales; every new message needs a `description` |
| `package.json` dependencies or `package-lock.json` | `npm install --package-lock-only --ignore-scripts`, then `npm ci --dry-run --no-audit --ignore-scripts` | pre-commit and CI both check the lockfile is in sync; never hand-edit it |
| any `{services,frameworks,tools}/**/*.{ts,tsx}` | `node tools/scripts/check-talent-reads.mjs` | ratchet on unprojected talent reads; pragma `// talent-full-doc: <reason>`; never hand-edit `.talent-reads-baseline.json` |
| an MCP tool definition in a service or framework | `npm run build:backends && npm run check:mcp-tool-names` | the baseline only shrinks |
| a `BEGIN/END_CRITICAL_SECTION` body in `service-workforce` `workers.proxy.ts` / `workers.client.ts` | `node tools/scripts/check-critical-methods.mjs`; when the change is intended, `--update` and commit `.critical-methods.json` | checksum gate |
| `services/service-employment/src/lib/data/_views/viewEmploymentProfiles/pipelineStages/` | bump `PIPELINE_VERSION` in `pipelineVersion.ts` | pre-commit blocks it otherwise |
| `.claude/skills/**` | `node tools/scripts/validate-skills.mjs` | CI `validate-claude-skills` |

Pre-commit also blocks, in added lines: barrel imports (`from '.'`,
`from '..'`) in `services|frameworks/*/src/**/*.ts` other than `index.ts`,
and `instance.create` in tests that import `waterworks-backend-dao` (use the
factories in `waterworks-backend-test-helpers`).

## Rules to read

Route rule files and skills by touched path with
`~/.claude/skills/wx-review/references/rule-routing.md`: its *Always*,
*Rules by touched path* and *Skills by touched area* tables. PRs from this
pipeline are reviewed by `/wx-review` against the same list.

## Quality tools

The same gates `/wx-review` runs, from `~/.claude/agents/references/`. Run
from `apps/wx-system`, once per touched workspace, over **application code
only**: never a `tools/<name>` workspace, never files under `scripts/` or
`migration(s)/`, never migration scripts by name. `FILES` is that list,
comma-separated, relative to the workspace. `BASE` is the base commit.

```sh
node ~/.claude/agents/references/complexity-gate.mjs --workspace <ws> --base $BASE --files $FILES \
  --ceiling 15 --warn 8 --delta 20 --min-drop 10 --json <tmp>/complexity.json
node ~/.claude/agents/references/dup-gate.mjs --workspace <ws> --base $BASE --files $FILES \
  --scan . --json <tmp>/dup.json
node ~/.claude/agents/references/coverage-gate.mjs --workspace <ws> --base $BASE --files $FILES \
  --threshold 90 --json <tmp>/coverage.json
```

- Complexity: `services/service-todo` sets a ceiling of **8** per function
  (`.claude/rules/todo-typescript.md`); use `--ceiling 8` there.
- Coverage: the Tester's targets apply (new files at least 90%, touched
  files no drop). `/wx-review` itself runs this gate at `--threshold 95
  --step 1 --step-max-lines 400 --min-fn-lines 10` and reports touched
  functions under 95; aim there when it is cheap.
- The coverage gate needs `.env`, `node_modules` and built `dist/` (setup
  step 2). A wx-ui run takes minutes: one long timeout, never `--no-cache`,
  never re-run with other flags to move a number.
- The repo has no coverage thresholds of its own and no CI coverage job.

## Never

- `npm test` or `npm run test:ci` at `apps/wx-system` level: every workspace.
- `npm test -w frontends/wx-ui -- <path>`: Vitest ORs the filter with `src`,
  so it runs the whole wx-ui suite. Use `test:file ... run <path>`.
- `npx jest` / `npx vitest` directly.
- `npm run check-types`: the root tsconfig has `files: []`, so it checks
  nothing.
- `npm run setup`, `update`, `clean*`, `reinit*`, `rebuild:*`: destructive or
  full clean rebuilds. Use `npx tsc -b` or `build:*`.
- `npm run pr-ready` as a check: it rewrites formatting, does full builds and
  never lints backend code.
- Anything that needs docker or a live broker: `test:atlas-local*`,
  `test:redpanda*`, `test:e2e`, `backend`, `resources*`. Those run in RWX.
- Playwright with `--ui`, `--debug` or `PWDEBUG=1`.

## Gotchas

- `Failed to resolve import "@fountain/wx-api-clients/generated/..."`: the
  generated clients are missing. Re-run setup step 2, or
  `npm run clients:prebuild`.
- `#1e2551e1 Missing required MongoDB environment variables`: no `.env`.
  Re-run setup step 2, or `npm run env`.
- `TS2305` from `@fountain/cdc-contracts`:
  `npm run refresh:cdc-contracts && npm install`.
- A test fails against old behavior of a framework you changed: its `dist/`
  is stale. `npx tsc -b frameworks/<name>` and re-run.
- Unit tests use `mongodb-memory-server`, no docker. The first run downloads
  or starts MongoDB and is slow: one long timeout, never escalating retries.
- Test time budgets (root `CLAUDE.md` § Writing tests): unit 100 ms,
  DB-backed 1 s, render 2 s, 5 s maximum. Prefer adding cases to an existing
  test file over a new one (each new file costs about 3 s).
- PR body: root `CLAUDE.md` § Pull requests. When the diff carries no test,
  the body says `No test: <reason>`.
