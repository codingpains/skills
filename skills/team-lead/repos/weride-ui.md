---
name: weride-ui
remote: github.com/codingpains/weride-ui
updated: 2026-10-07
---

# weride-ui

The WeRide frontend: an npm workspaces + Turborepo monorepo, Node 24
(`.nvmrc`), npm 11. Workspaces (use the path with `-w`, the package name with
turbo `--filter`):

| Path | Package | What | Port |
|---|---|---|---|
| `apps/rider-app` | `@weride/rider-app` | Next 16, i18n ES+EN (next-intl) | 3001 |
| `apps/partner-app` | `@weride/partner-app` | Vite SPA, Spanish only | 3002 |
| `apps/driver-app` | `@weride/driver-app` | Vite SPA, Spanish only | 3003 |
| `apps/admin-app` | `@weride/admin-app` | Next 16, Spanish only | 3004 |
| `packages/ui` | `@weride/ui` | the design system, Storybook | 6006 |
| `packages/api-client` | `@weride/api-client` | client generated from weride-api's contract | |
| `packages/tailwind-config` | | tokens (`shared-styles.css`), no scripts | |

Packages are consumed as TypeScript source: nothing needs building before a
typecheck or a test. **Every command runs from the worktree root** unless it
says otherwise. The checkout lives in the `weride-go` workspace (profile
`weride-go`), next to `weride-api`, whose `swagger/v1/swagger.yaml` is the
only interface between the two.

The merge gate is `.github/workflows/ci.yml`, one job:
`npm ci`, `npm run format:check`, `npx turbo run lint typecheck test build`.
CI never generates the client: a stale client is caught only locally.

The rules live in `CLAUDE.md` (§ The API contract, § Frontend conventions,
§ Using @weride/ui, § Testing). The Next apps' `AGENTS.md` adds one: read
`node_modules/next/dist/docs/` before writing Next code, since Next 16 breaks
older habits. There is no `.claude/rules/`. `AGENTS.md` mirrors `CLAUDE.md`:
a change to one is a change to both.

## Worktree setup

One command, run as the Lead's single background setup call (SKILL.md § 0
step 7):

`bash ~/.claude/skills/team-lead/repos/weride-ui.setup.sh <main checkout> <worktree> [--spec <swagger.yaml>]`

About 2–10 s. It checks Node against `.nvmrc`; copies every `node_modules`
copy-on-write with `bootstrap-worktree.sh` (`no .env files` is expected:
tests mock the API with MSW and need none); runs `npm ci` when the lockfile
differs from the main checkout's; writes the weride-api contract to
`node_modules/.cache/weride-api/swagger.yaml`; and reports whether
`src/generated` matches it. The log ends in
`setup: ok (WERIDE_API_SPEC=<path>)`.

- The contract defaults to weride-api's `origin/main`. For a full-stack
  ticket whose weride-api half is not merged yet, pass
  `--spec <weride-api worktree>/swagger/v1/swagger.yaml` (profile `weride-go`).
- Why: `packages/api-client/spec-path.ts` looks for `<repo>/../weride-api`,
  which from `weride-ui-worktrees/<ticket>` does not exist. Then
  `generate:api` fails, and the lefthook `openapi` hook and
  `generated-parity.test.ts` **skip without failing**, so a green test run
  proves nothing about the client. Every command touching the client takes
  `WERIDE_API_SPEC=$PWD/node_modules/.cache/weride-api/swagger.yaml`.
- `parity FAILS` is a fact for the Architect, not a setup failure: on
  2026-10-07 `origin/main`'s client was 486 lines behind the contract.

Git hooks (lefthook, shared with the main checkout) run on every commit:
prettier on staged files, `npx turbo run lint` over the whole repo, and the
`openapi` hook when `packages/api-client` config changes.

## Checks by change

| Changed | Run | Notes |
|---|---|---|
| any file prettier covers | `npx prettier --check <files>` (fix: `npx prettier --write <files>`) | from the root. CI runs `prettier --check .` |
| `.ts/.tsx` in a workspace | `cd <workspace> && npx eslint <files>`; for partner, driver, ui and api-client add `--max-warnings 0` | their lint scripts carry it; the Next apps' do not. rider-app prints 3 pre-existing `no-img-element` warnings |
| source in a workspace | `npm run typecheck -w <workspace>` (2–4 s); the tests beside the touched files: `npm run test -w <workspace> -- <test paths relative to the workspace>` | partner and driver typecheck with `tsc -b`, the others `tsc --noEmit`; no per-file typecheck |
| `packages/ui` | the above for `packages/ui`; `npm run test -w packages/ui` (includes `figma-parity.test.ts`, `tokens.test.ts`); then typecheck and tests of each app that imports the changed component (`rg -l "@weride/ui/components/<file>" apps`) | a component change needs its story and its `figma-inventory.ts` entry, or the parity test fails |
| `packages/api-client` (not `src/generated`) | the above; `WERIDE_API_SPEC=$PWD/node_modules/.cache/weride-api/swagger.yaml npm run test -w packages/api-client` | without the variable the parity test skips |
| rider-app or admin-app routing, layouts, `next.config`, middleware/proxy | also `npm run build -w <workspace>` | Next catches route and server/client-boundary errors only at build |
| a change for a commit that ends the stage | `npm run format:check && npx turbo run lint typecheck test build` | the CI gate, about 15 s warm, a minute cold |
| test files only | the test files; prettier and eslint on them | vitest compiles them; `tsc` covers them where the tsconfig includes `src` |

## Conditional checks

| When this changes | Also run | Why |
|---|---|---|
| the ticket needs an operation, field or code the client lacks | `WERIDE_API_SPEC=$PWD/node_modules/.cache/weride-api/swagger.yaml npm run generate:api`, review `git diff --stat packages/api-client/src/generated`, run the api-client tests, commit the generated files alone (`chore(api-client): regenerate from weride-api <sha> (WERIDE-NN)`) | never hand-edit `src/generated`. A regenerate also pulls every other contract change since the last one: name them in the report. When the operation is not in weride-api's `origin/main` either, stop: the backend half comes first (profile `weride-go`) |
| a command call | an `Idempotency-Key` from `newIdempotencyKey()`, one per logical action; branch on `error.code`, never the message; optimistic update only for commands in `OPTIMISTIC_COMMANDS` | `CLAUDE.md` § The API contract |
| a request a test triggers | a handler in the app's `src/mocks/handlers.ts` | `onUnhandledRequest: 'error'`: never loosen it |
| a rider-app string | both `messages/es.json` and `messages/en.json`; `npm run test -w apps/rider-app -- src/i18n` | `messages.test.ts` checks parity and the verbatim Spanish acceptance copy. The other apps are Spanish-only: never add i18n there |
| a shared component or token | its story titled `Components/<Figma name verbatim>`, its `figma-inventory.ts` entry; `npx shadcn@latest add <name>` only inside `packages/ui` | `figma-parity.test.ts` |
| a new client-guarded route in rider-app | the edge proxy's protected segments | a client-only guard lets a cookieless guest reach the page first (WERIDE-97) |
| `package.json` / `package-lock.json` | `npm install` at the root, then `npm ci --dry-run` (unverified) | never hand-edit the lockfile |

## Rule greps

Findings reviews kept making. The Hardener runs them on the whole diff before
its first edit, the Tester on its own commits. Resolve every hit, or name it
under *Left alone on purpose* with the reason. `BASE` is the base commit.

- A banned Tailwind class (`CLAUDE.md` § Reviewing your own diff: must print
  nothing):
  `git diff $BASE...HEAD -U0 -- apps packages/ui | rg '^\+.*className=.*\b(text-(xs|sm|base|lg|xl|[0-9]xl)|font-(semi)?bold|(text|bg|border)-(gray|zinc|slate|red|blue|neutral|stone)-[0-9]|[a-z]-\[[0-9]+px\])'`
- Session tokens in web storage (decision of WERIDE-37; WERIDE-81 and 82):
  `git diff $BASE...HEAD -U0 -- apps ':!*.test.*' | rg '^\+.*(zustand/middleware|localStorage\.|sessionStorage\.|indexedDB|document\.cookie)'`
- A comment line over 100 columns (prettier's `printWidth`; prettier does not
  rewrap comments; WERIDE-96, 81):
  `git diff $BASE...HEAD -U0 -- apps packages | rg '^\+\s*(//|\*|/\*).{0,}$' | awk 'length > 101'`
- Leftovers: `git diff $BASE...HEAD -U0 -- apps packages | rg '^\+.*(console\.(log|debug)|debugger|\.only\(|\bTODO\b|FIXME)'`
- A plan label in code or a test name (ticket IDs are allowed: the repo uses
  them in gap comments):
  `git diff $BASE...HEAD -U0 -- apps packages | rg '^\+.*\b(AC[0-9]+|[BDG][0-9]{1,2})\b'`

## Quality tools

The repo has no coverage provider, complexity or duplication check. Use the
script beside this profile; it installs its tools once into
`~/.cache/team-lead/` (pinned to the worktree's vitest) and never touches
tracked files:

```sh
Q=~/.claude/skills/team-lead/repos/weride-ui.quality.sh
bash $Q <worktree> coverage <workspace> <test files> -- <source files>   # paths relative to <workspace>
bash $Q <worktree> complexity <files>      # sonarjs cognitive complexity: lists > 8, fails > 15
bash $Q <worktree> dup <files or folders>  # jscpd, 5 lines / 50 tokens: fails on any clone
```

- Coverage prints statements, branches, functions and uncovered lines per
  source file. Targets are the Tester's (new files at least 90%, touched
  files no drop). For the base number, run the same command in a detached
  worktree of the base commit set up with `weride-ui.setup.sh`.
- Complexity: run it on touched non-test source files. Over 15 is a
  must-fix; 9–15 is a warning to name.
- Duplication: run it over the touched files plus the folder they live in,
  so a copy of nearby code shows.

## UI

For any change that can move a pixel.

- **Design system**: `@weride/ui` in `packages/ui/src/components/*.tsx`,
  tokens in `packages/tailwind-config/shared-styles.css`. The list of
  components, story titles and required states is `FIGMA_COMPONENTS` in
  `packages/ui/src/foundations/figma-inventory.ts`: read it, not the whole
  package.
- **Rules to read before the first visual edit**: `CLAUDE.md` § Using
  @weride/ui, whole. In short: an app assembles, it does not draw; semantic
  tokens only; app-local wrappers bind router, locale and store and add no
  visual classes; screens get chrome from `<Screen header=…>`; a gap with no
  Figma node stays app-local with a comment naming it and the ticket
  (`apps/rider-app/src/components/consent-checkbox.tsx`).
- **Figma**: the user story's `Figma Link`; `get_metadata` on the frame
  lists layer names, which are the component names. An
  `<instance name="X">` means the code renders `X` from `@weride/ui`.
- **Render a component**: Storybook. From `packages/ui`,
  `npx storybook dev -p <free port> --ci --no-open > <tmp>/sb.log 2>&1` in
  the background, wait for `curl -sf http://localhost:<port>/iframe.html`,
  then capture with headless Chrome:
  `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars --window-size=390,844 --force-device-scale-factor=2 --virtual-time-budget=8000 --screenshot=<out.png> "http://localhost:<port>/iframe.html?id=<story id>&viewMode=story"`.
  Story ids are `components-<title>--<story>` in kebab case. Stop it after:
  `pkill -f "storybook dev -p <port>"`. Pick a free port: 6006 may be the
  human's.
- **Render a page**: no Playwright, and rider-app has no MSW browser worker,
  so a page that calls the API needs the backend or stubs. Add a scaffolding
  route that mounts the screen with fixed props
  (`apps/rider-app/src/app/[locale]/zz-preview/page.tsx`), run
  `npx next dev -p <free port>` in `apps/rider-app`, capture as above at
  390x844. Delete the route before your last commit. The Vite apps:
  `npx vite --port <free port>` in the app, same idea.
- Headless Chrome needs the Bash sandbox off on macOS.

## Never

- Hand-edit `packages/api-client/src/generated`, or run `generate:api`
  without `WERIDE_API_SPEC` from a worktree.
- `npx shadcn@latest add` inside an app.
- i18n scaffolding in partner, driver or admin.
- Loosen MSW's `onUnhandledRequest: 'error'`.
- Commit a preview route, a capture, or anything under `node_modules`.
- `timeout` and GNU `sed -i` (macOS: `sed -i ''`).
- `npm run dev` (every app at once, fixed ports) or `npm run storybook`
  (fixed port 6006): start the one server you need on a free port.

## Gotchas

- `react-hooks/refs` forbids reading a ref during render: hold the value in
  `useState`.
- `vi.spyOn` on a Zustand store action breaks later tests: a `setState`
  copies the spy into a new state object `restoreAllMocks` cannot reach.
  Restore the real action in `afterEach` (WERIDE-50).
- driver-app needs `afterEach(cleanup)` in `src/test/setup.ts`.
- A `router.replace` guard races a hard `location.assign` in jsdom: wrap the
  screen in the app's session gate rather than asserting on order.
- Fixed heights clip long copy (`h-12 truncate` on the toast): render
  Spanish copy, the longest, before calling a layout done.
- The partner and driver apps are Vite SPAs (no Next, no Capacitor shell
  yet).
- Commit subjects: `<type>(<scope>): <subject> (WERIDE-NN)`, the convention in
  `git log origin/main`; PR titles `[WERIDE-NN] <type>: <subject>` (profile
  `weride-go` § Conventions).
