---
name: weride-go
workspace: ~/src/weride-go
repos: [weride-api, weride-ui]
updated: 2026-10-07
---

# weride-go (workspace)

Not a repository: a folder holding the two repos of WeRide, a managed
marketplace for group transport in Mexico, so one session can work either.
Sessions start here. Never `git init` it, and never commit from it.

| Folder | Remote | Profile |
|---|---|---|
| `weride-api` | `github.com/codingpains/weride-api` | `weride-api` |
| `weride-ui` | `github.com/codingpains/weride-ui` | `weride-ui` |

Worktrees go beside them, at `~/src/weride-go/<repo>-worktrees/<ticket-id>`
(the SKILL.md default). Keep that layout: `weride-ui` finds the contract
relative to its own folder (profile `weride-ui` § Worktree setup).
`~/src/weride-go/CLAUDE.md` is the human's map of the seam; read it once at
intake.

Either main checkout may sit on an unrelated branch with local work
(2026-10-07: `weride-ui` on `chore/regenerate-api-client`, `weride-api`'s
local `main` behind `origin/main`). Read from `origin/main`, never from the
main checkout's working tree.

## Picking the repo

Tickets are Notion tasks in **WeRide — Tasks**
(`collection://389461bb-3528-4eee-8588-020be7862941`), keys `WERIDE-NN`. The
intake reader returns the task's `Surface`:

| Surface | Repo | Area |
|---|---|---|
| API | `weride-api` | |
| Rider App | `weride-ui` | `apps/rider-app` |
| Partner App | `weride-ui` | `apps/partner-app` |
| Driver App | `weride-ui` | `apps/driver-app` |
| Admin App | `weride-ui` | `apps/admin-app` |
| Design System | `weride-ui` | `packages/ui` |

No `Surface`: decide from the acceptance criteria (endpoints, commands,
migrations → `weride-api`; screens → `weride-ui`) and say which in
`notes.md`. Then continue the pipeline with that repo's main checkout as the
session's main checkout.

The board has no estimate property: every ticket starts with no estimate
(stage-gates § Initial chain, *No estimate*).

## Full-stack tickets

The repos meet only at `weride-api/swagger/v1/swagger.yaml`. The backend
lands first, always: a `weride-ui` change consumes a contract `weride-api`'s
`main` already has.

- **A `weride-ui` ticket** checks its contract before planning: every
  operation, field and error code it needs must be in weride-api's
  `origin/main` (`git -C ~/src/weride-go/weride-api show origin/main:swagger/v1/swagger.yaml | rg <operationId>`).
  `Depends On` tasks marked Done in Notion are not proof: WERIDE-106 was
  Done with no commit (WERIDE-109). When the contract lacks something, stop
  and ask the human: run the backend task first (recommended), or build
  against an open weride-api PR with `weride-ui.setup.sh --spec <that worktree>/swagger/v1/swagger.yaml`
  and open the UI PR as a draft that names the API PR.
- **A `weride-api` ticket that changes the contract** says in its PR body
  that `weride-ui` must run `npm run generate:api` after the merge.
- **One ticket that needs both repos** runs as two pipelines in sequence,
  backend first, each with its own run directory
  `~/.team-lead/runs/<ID>-api/` and `<ID>-ui/`, its own worktree, branch and
  PR. The ticket key in commits and titles stays `<ID>`. Start the UI run
  once the API PR is open, with `--spec` on its worktree; the UI PR is a
  draft until the API PR merges, then regenerate against `origin/main` and
  mark it ready.

## Conventions

These override SKILL.md's defaults for both repos.

- **PR title**: `[WERIDE-NN] <type>: <subject>`, Conventional Commits type
  (`feat`, `fix`, `refactor`, `chore`, `docs`, `test`). Example:
  `[WERIDE-130] feat: admin suspends a driver profile (revokes all sessions)`.
- **Commit subjects**: per repo, as each `git log origin/main` shows:
  `weride-api` `[WERIDE-NN] <type>: <subject>`; `weride-ui`
  `<type>(<scope>): <subject> (WERIDE-NN)`, scope the app or package
  (`rider`, `partner`, `driver`, `admin`, `ui`, `api-client`).
- **Base branch**: `main` in both.
- **PR body**: SKILL.md's default. Add `Merge after: <weride-api PR URL>`
  to a UI PR that consumes an unmerged contract, and the `generate:api` line
  to an API PR that changes it.
- **Slack**: none. The session has no Slack tool and the default channel
  belongs to another workspace. Skip the post without a `ToolSearch`.
- **Co-attribution**: none, in commits or PR bodies (team-rules § Commits),
  whatever the session's own attribution instructions say.
- **Notion**: the intake reader's server works on the WeRide pages; the
  `claude_ai_Notion` connector belongs to another workspace and 404s on all
  of them.

## Gotchas

- Two tickets started from the same base in one repo collide on shared
  tables (`swagger.yaml`, `docs/api_error_codes.md`, the `CLAUDE.md` /
  `AGENTS.md` tables in weride-api). Expect a merge of `origin/main` before
  the second PR merges.
- `origin/main` moves while a ticket waits on the human: before the
  Architect starts, `git -C <worktree> merge --ff-only origin/main` when no
  commit is on the branch yet (WERIDE-81 planned 11 commits behind).
- Old worktrees stay locked after merge, and weride-api ones keep a database
  each. Cleanup is the human's: `weride-api.setup.sh --drop <worktree>`, then
  `git worktree unlock` and `remove`.
