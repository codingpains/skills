---
name: megalith-wx-system
remote: github.com/onboardiq/megalith
paths: [apps/wx-system/]
updated: 2026-09-30
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

One command, run as the Lead's single background setup call (SKILL.md § 0
step 7):

`bash ~/.claude/skills/team-lead/repos/megalith-wx-system.setup.sh <main checkout> <worktree> [--ui] [--check <workspace>]...`

- `--ui` when the ticket, a plan block or a review item touches
  `frontends/`. When unsure, pass it: it adds about a minute.
- `--check <workspace>` for each `services/` or `frameworks/` workspace the
  ticket changes, for example `--check services/service-todo`.

It stops at the first failure and runs, in order:

1. Node from `apps/wx-system/.nvmrc` (v24.15.0).
2. `~/.claude/skills/team-lead/scripts/bootstrap-worktree.sh`: every `.env`
   and every `node_modules` (copy-on-write) from the main checkout,
   including the repo-root one, where lefthook lives. Then it checks
   lefthook is there: without it, git hooks (lint-staged, the ticket
   prefix, the barrel-import check) silently do nothing.
3. `npm ci` in `apps/wx-system` when its `package-lock.json` differs from
   the main checkout's.
4. A rebuild of `@fountain/cdc-contracts` from this worktree's source into
   `apps/wx-system/node_modules`. It is installed as a copy, so it comes
   from the main checkout's branch, and a newer base fails with `TS2305`.
5. With `--ui`: `npm run clients:prebuild` (the generated API clients),
   then wx-ui's `i18n:compile:local` and `formatjs:compile:src` (the
   compiled translations the type check reads).
6. With `--check`: `npx tsc -b <workspace>`. On `TS2307` for an installed
   package (the main checkout was pulled but not reinstalled), it runs
   `npm ci` once and checks again.

The log ends in `setup: ok`, or in `setup: failed at <step>` with the error.
Re-running it is safe. The bootstrap also names other lockfiles that
differ: other megalith apps (`apps/hire`, ...), and `packages/ripple` and
`packages/universal-search`, which wx-system reads through its own
installed copies (its `npm ci` rebuilds them). Ignore those lines:
`setup: ok` is the only lockfile check that counts here. Never repair a
failure with `npm install`: it rewrites `package-lock.json`.

Built output (`dist/`) is not copied. Before running a workspace's tests,
build it and what it depends on: `npx tsc -b <workspace>` (incremental, fast
after the first run).

## Checks by change

| Changed | Run | Notes |
|---|---|---|
| any `.ts/.tsx/.js/.mjs/.cjs/.json/.yml` file | `npx oxfmt --check <files>` (fix: `npx oxfmt <files>`) | CI runs `oxfmt --check .`; Prettier is inactive |
| any `.ts/.tsx/.js` file | `npx oxlint --type-aware --max-warnings 0 <files>` | the commit hook lints **without** `--type-aware`, so type-aware errors only show in CI unless you run this |
| `services/<name>` or `frameworks/<name>` source | `npx tsc -b <workspace>`; then `STAGE=test npm test -w <workspace> -- <test paths>` for the touched tests and the tests beside touched files | always `npm test`, never `npx jest`/`npx vitest`: the script carries `--forceExit`, `--passWithNoTests` and log settings. Jest or Vitest depends on the workspace. Prefix every test run with `STAGE=test`: without it, the test Mongo setup never starts and the run hangs. In `services/service-todo` also prefix `CI=true`: without it, AMQP setup in `topic.initializer.ts` times out after 10 s and skips every test |
| `frameworks/<name>` source | also `npm run compile:backends`, and the tests of dependents that call the changed code (`rg "@fountain/<name>"`) | dependents import the framework's built `dist/` |
| `frontends/wx-ui` | `npm run typecheck -w frontends/wx-ui`; tests: `npm run test:file -w frontends/wx-ui -- run <paths>` | needs generated clients and compiled translations (setup with `--ui`) |
| `tools/tool-ecosystem` | `npx tsc -b tools/tool-ecosystem`; `npm test -w tools/tool-ecosystem -- <paths>` | the other `tools/*` have no tests that CI runs |
| test files in `services/<name>` | the test files as above; oxfmt and oxlint on them; `npx tsc -b <workspace>` | service tsconfigs include their tests, and `oxlint --type-aware` does not report compiler errors (`TS2322`, `TS2741`): skipping `tsc` lets a broken test reach CI |
| test files in `frameworks/<name>` | the test files as above; oxfmt and oxlint on them | framework tsconfigs exclude tests, so `tsc` never checks them |
| a new `@fountain/<workspace>` import | `node scripts/check-tsconfig-refs.js` | fails when the tsconfig reference is missing |

## Conditional checks

| When this changes | Also run | Why |
|---|---|---|
| a route, schema, `*.openapi.ts` or anything under `routes/` that the frontend consumes | `npm run build:backends && npm run clients && npm run compile:frontends` | clients are gitignored (nothing to commit) but wx-ui must still compile against them |
| `frameworks/waterworks-backend-hire-internal`, `-hire-public-v2`, or `apps/hire/swagger/{internal_api,api/v2}/fountain.yaml` | `npm run codegen`, commit `frameworks/*/generated` | CI `hire-sdk-diff` fails on stale generated SDKs; never hand-edit them |
| a `*.template.yml` (permissions) | `npm run rebuild:authz`, commit what it changes (unverified) | `apps/wx-system/CLAUDE.md` § Commands |
| an i18n message in wx-ui | `npm run i18n:extract:source -w frontends/wx-ui`, commit only `src/i18n/translations/en-US.json`; then `npm run formatjs:compile -w frontends/wx-ui && npm run i18n:check -w frontends/wx-ui` | never commit other locales; every new message needs a `description` |
| `package.json` dependencies or `package-lock.json` | `npm install --package-lock-only --ignore-scripts`, then `npm ci --dry-run --no-audit --ignore-scripts` | never hand-edit it. The pre-commit hook re-runs `npm install --package-lock-only` and rejects any other lockfile, so npm's output is the only one that commits. npm may also rewrite hundreds of unrelated lines (it records the root `overrides`): run the same install on a clean base first, and if the churn shows there too, it is npm's. Commit it, check no installed `version` changed, and say so in the PR body. It is not a question for the human |
| any `{services,frameworks,tools}/**/*.{ts,tsx}` | `node tools/scripts/check-talent-reads.mjs` | ratchet on unprojected talent reads; pragma `// talent-full-doc: <reason>`; never hand-edit `.talent-reads-baseline.json` |
| an MCP tool definition in a service or framework | `npm run build:backends && npm run check:mcp-tool-names` | the baseline only shrinks |
| a `BEGIN/END_CRITICAL_SECTION` body in `service-workforce` `workers.proxy.ts` / `workers.client.ts` | `node tools/scripts/check-critical-methods.mjs`; when the change is intended, `--update` and commit `.critical-methods.json` | checksum gate |
| `services/service-employment/src/lib/data/_views/viewEmploymentProfiles/pipelineStages/` | bump `PIPELINE_VERSION` in `pipelineVersion.ts` | pre-commit blocks it otherwise |
| `.claude/skills/**` | `node tools/scripts/validate-skills.mjs` | CI `validate-claude-skills` |

Pre-commit also blocks, in added lines: barrel imports (`from '.'`,
`from '..'`) in `services|frameworks/*/src/**/*.ts` other than `index.ts`,
and `instance.create` in tests that import `waterworks-backend-dao` (use the
factories in `waterworks-backend-test-helpers`).

**service-security tests.** `CI=true` does not help there:
`tests.initializer.ts` always creates a broker topic, so every test file
hangs about 30 s and fails with `#d89b17c5`. Run its tests through the
no-broker config, which drops only the topic setup:
`STAGE=test npm test -w services/service-security -- --config ~/.claude/skills/team-lead/repos/megalith-wx-system.jest-security.cjs <paths>`.
A test that publishes events also installs the in-memory messaging stand-in
(`src/lib/initializers/in-memory-messaging.initializer.ts`, `ci-testing`
skill). `tokens.utils.test.ts` imports the topic setup itself and always
fails locally. The coverage gate cannot run in this workspace: measure with
`--coverage` through the same config, and say so in the report.

## Rules to read

Route rule files and skills by touched path with
`~/.claude/skills/wx-review/references/rule-routing.md`: its *Always*,
*Rules by touched path* and *Skills by touched area* tables. PRs from this
pipeline are reviewed by `/wx-review` against the same list.

## Rule greps

Rules that reviews keep finding, as searches over the added lines. The
Hardener runs them on the whole diff before its first edit, and the Tester
on its own commits before it reports. Resolve every hit, or name it under
*Left alone on purpose* with the reason. From `apps/wx-system`:

- A cast in service-todo source (`todo-typescript.md` § Validate: never
  cast):
  `git diff $BASE...HEAD -U0 -- services/service-todo/src ':!*.test.ts' | rg '^\+.*\bas [A-Z]'`
- A `||` default in service-todo (`todo-typescript.md`: use `??`):
  `git diff $BASE...HEAD -U0 -- services/service-todo/src | rg '^\+.*\|\| '`
- A new database read (`backend.md` § MongoDB reads: each needs a `limit`,
  or a one-line comment that proves the bound):
  `git diff $BASE...HEAD -U0 -- services frameworks ':!*.test.ts' | rg '^\+.*\.(find|findOne|findBatched|aggregate|__unsafeFind)\('`
- A plain read on a locked DAO (§ Gotchas, *Locked DAOs*). A hit in code
  another service reaches (a client method, anything the service's index
  exports, another service's code) is a must-fix. List the locked DAOs with
  `rg -n '^\s*[\w.]+\.dao\.lock\(\)' services/*/src/index.ts`, then the new
  plain reads with
  `git diff $BASE...HEAD -U0 -- services ':!*.test.ts' | rg '^\+.*\.dao\.instance\.(find|findOne|count|aggregate)\('`.
- A ticket ID, AC number or plan label in a comment or test name (root
  `CLAUDE.md` § Writing style; a lint suppression directive is the one
  allowed case):
  `git diff $BASE...HEAD -U0 | rg '^\+.*(//|/\*|\* |it\(|test\(|describe\().*\b(AC[0-9]+|[STDF][0-9]{1,2}|[A-Z]{2,5}-[0-9]+)\b'`

## Quality tools

The same gates `/wx-review` runs, from `~/.claude/agents/references/`. Run
from `apps/wx-system`, over **application code only**: never a
`tools/<name>` workspace, never files under `scripts/` or `migration(s)/`,
never migration scripts by name, never test files. `BASE` is the base
commit.

Complexity and coverage run once per touched workspace, with `FILES` that
workspace's list, comma-separated, relative to the workspace. Duplication
runs **once for the whole change**, with `ALL_FILES` every touched
application file, relative to `apps/wx-system`: each run scans all of
`apps/wx-system` (about 18,000 files, about 70 s) whatever the workspace, so
one run per workspace repeats the same scan.

```sh
node ~/.claude/agents/references/complexity-gate.mjs --workspace <ws> --base $BASE --files $FILES \
  --ceiling 15 --warn 8 --delta 20 --min-drop 10 --json <tmp>/complexity.json
node ~/.claude/agents/references/dup-gate.mjs --workspace . --scan . --base $BASE --files $ALL_FILES \
  --json <tmp>/dup.json
STAGE=test node ~/.claude/agents/references/coverage-gate.mjs --workspace <ws> --base $BASE --files $FILES \
  --tests $TESTS --threshold 90 --json <tmp>/coverage.json
```

- Complexity: `services/service-todo` sets a ceiling of **8** per function
  (`.claude/rules/todo-typescript.md`); use `--ceiling 8` there.
- Coverage: prefix the same variables the workspace's tests need
  (§ Checks by change: `STAGE=test` always, and `CI=true` in service-todo).
  `TESTS` is every test file beside a touched file plus every test file the
  branch added or changed in that workspace, comma-separated, relative to
  the workspace. Without `--tests` the gate runs every test that imports a
  touched file, which for a widely imported file is most of the suite
  (service-todo: about 1,900 tests and 160–250 s per side, against about
  25 s). On ONB-1304 both ways gave the same numbers. When a touched file
  shows `no test exercises this file` but is tested elsewhere, re-run that
  workspace without `--tests` and say so.
- Coverage targets: the Tester's apply (new files at least 90%, touched
  files no drop). `/wx-review` itself runs this gate at `--threshold 95
  --step 1 --step-max-lines 400 --min-fn-lines 10` and reports touched
  functions under 95; aim there when it is cheap.
- The coverage gate needs the `.env` files, `node_modules` and built `dist/`
  that setup copies. Never check for `.env` yourself (team-rules
  § Scope): a missing one fails with `#1e2551e1` (§ Gotchas). A wx-ui run
  takes minutes: one long timeout, never `--no-cache`, never re-run with
  other flags to move a number.
- The repo has no coverage thresholds of its own and no CI coverage job.

## UI

For any change under `frontends/wx-ui` that can move a pixel. Paths in this
section are relative to the **worktree root** (megalith), not
`apps/wx-system`.

- **Design system**: Ripple (`packages/ripple`, `@fountain/ripple` in wx-ui),
  MUI and Tailwind. Reuse before building; the component-sourcing ladder is
  in `.claude/skills/prototype-to-implementation/SKILL.md`.
- **Rules to read before the first visual edit**, in order, from
  `.claude/skills/ux-design/`: `constraint-anti-pattern-guard` (wins on
  conflict), `layout-composition`, `content-hierarchy`, `copywriting-voice`,
  `fountain-product-context`. When the ticket has a design, also
  `.claude/skills/prototype-to-implementation/SKILL.md` (which source wins,
  tokens, what to do when the design has a gap).
- **Render**: `.claude/skills/visual-harness/SKILL.md` with its wx-ui recipe
  `references/wx-ui.md`. It mounts one real component on localhost with only
  the data layer stubbed: no backend, no docker. Only 3% of wx-ui components
  have stories, so the harness is the default. When a story covers the
  state, from `apps/wx-system/frontends/wx-ui` run
  `npx storybook dev -p <free port> --ci --no-open` (the npm script hardcodes
  6006, which another worktree may hold). Harness files are scaffolding:
  never commit them.
- **Capture** (Playwright, headless Chromium):
  `node .claude/skills/prototype-conformance/scripts/capture.mjs --url <url> --viewport 1512x982 --shot <out.png> [--element <selector>] [--measure <selector>]`.
  Its header documents `--click`, `--steps` and `--init` to reach a state.
  Side by side: `node .claude/skills/prototype-conformance/scripts/compose.mjs --out <cmp.png> <design.png> <shipped.png> --labels "Design|Build"`.
  Headless Chromium needs the Bash sandbox off on macOS. Rendering pitfalls
  (fonts, stubs, viewport):
  `.claude/skills/implement-prototype-ticket/references/render-paths.md`.
- **Prototypes in the repo**: `designs/<project>/`. Read in the order
  `designs/CLAUDE.md` gives (`HANDOFF.md`, `CHANGELOG.md`, then the screen's
  source). A prototype named by the ticket is a design source like Figma.
  Resolve its colors with `node tools/design-sync/tokens.mjs --project <project>`.
- **Before the last commit** of a UI change: the checks in
  `.claude/skills/frontend-pre-pr/SKILL.md` (i18n extraction, oxfmt).

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

- A commit subject without `[<KEY>]:` means the git hooks did not run.
  Re-run setup; never amend around it.
- `Failed to resolve import "@fountain/wx-api-clients/generated/..."`: the
  generated clients are missing: setup ran without `--ui`. Run
  `npm run clients:prebuild`.
- `#1e2551e1 Missing required MongoDB environment variables`: no `.env`.
  Re-run setup, or `npm run env`.
- `TS2305` from `@fountain/cdc-contracts`: re-run setup. Never
  `npm install`: it rewrites `package-lock.json`.
- **Locked DAOs.** A service's `src/index.ts` calls `lock()` on the DAOs it
  exports and on its own DAOs other services read (service-authorization
  locks `data.matrices`; service-security locks `data.users`). Once that
  index loads, `dao.instance.find`, `findOne` and `count` throw `#540b9a12`.
  Code that another service or a client method reaches reads them with
  `__unsafeFind` / `__unsafeFindOne` and `{ __overrideLockMode: true }`
  (`.claude/skills/dao/SKILL.md` § cross-service reads; some DAOs cannot
  take the flag). A test that spies on `find`, or imports a client by file
  path instead of through the service's index, never meets the lock, so a
  green test proves nothing here.
- A test fails against old behavior of a framework you changed: its `dist/`
  is stale. `npx tsc -b frameworks/<name>` and re-run.
- A test run with no output after 30 s is a missing `STAGE=test`, not a
  slow MongoDB start. Stop it and re-run with the variable. Never search the
  disk for Mongo binaries.
- Test time budgets (root `CLAUDE.md` § Writing tests): unit 100 ms,
  DB-backed 1 s, render 2 s, 5 s maximum. Prefer adding cases to an existing
  test file over a new one (each new file costs about 3 s).
- PR body: root `CLAUDE.md` § Pull requests. When the diff carries no test,
  the body says `No test: <reason>`.
