# Repo profiles

A repo profile tells every agent exactly which checks to run for a change in
one repository, or one part of a monorepo, and how to set up a worktree for
it. Without a profile, agents work the commands out from the repo each time
(`team-rules.md` § Validations). With one, they start from commands that are
already known to work.

Profiles live in `~/.team-lead/repos/<name>.md`, on this machine only, next
to the runs: never in the skills repo, never in the target repository. Their
helper files (a setup script, a coverage or test config) sit beside them,
named `<name>.<what>.<ext>`, and the profile calls them by that full path.
A missing folder means no profiles yet. A `run.json` that lists a profile
inside the skill's own folder (`.../team-lead/repos/`) is from before the
move: read the same file name under `~/.team-lead/repos/`.

## Matching

Match by the repository's remote, not by folder path: each ticket runs in its
own worktree, so the folder differs from run to run.

1. Take `git -C <main checkout> remote get-url origin` and normalize it to
   `host/owner/repo`: drop the `git@` or `https://` prefix and the `.git`
   suffix, and turn `host:owner` into `host/owner`.
   `git@github.com:onboardiq/megalith.git` → `github.com/onboardiq/megalith`.
2. Every profile whose `remote` equals it applies to this repo.
3. A profile with `paths` covers only files under those paths. An agent uses,
   for each file it touched, the profile whose `paths` contain it. A file no
   profile covers falls back to discovery.

## Format

```markdown
---
name: <file name without .md>
remote: github.com/<owner>/<repo>
paths: [apps/wx-system/]        # optional; omit for the whole repo
updated: YYYY-MM-DD             # the date the commands were last checked
---

# <repo> / <area>

One paragraph: what this area is, its package manager, where commands run
from (for example "every command runs from apps/wx-system").

## Worktree setup
Commands that make a fresh worktree able to lint, typecheck and run unit
tests. Replaces the generic bootstrap script when present.

## Merge of main
Optional: what a merge commit of the default branch needs before the
commit hook accepts it (installs for the folders main changed, lockfile
checks), for review rounds that bring main in.

## Checks by change
| Changed | Run | Notes |
|---|---|---|
| source files in one workspace | lint on the files; typecheck for the workspace; the touched test files | |
| test files only | the test files; lint on them | |
| ... | ... | |

Exact, copy-pasteable commands with placeholders (`<files>`, `<workspace>`,
`<test-file>`). File-scoped wherever the tool allows it.

## Conditional checks
| When this changes | Also run | Why |
|---|---|---|
| a translation string | the extract command, and commit the catalog | CI fails on a stale catalog |

## Rules to read
Optional: where the rule files and skills for each touched path are listed,
when the repo has more than `.claude/rules` globs can express.

## Quality tools
Complexity, duplication and coverage commands and thresholds, for the
Hardener and the Tester.

## UI
Optional, for repos with a frontend: the design system and where its
components live, the UI rules to read before a visual change, how to render
one component or page without the whole stack, how to capture it, and where
design prototypes live in the repo.

## Conventions
Optional: where the repo's own conventions differ from SKILL.md's defaults:
the PR title format, the Slack channel (or `Slack: none`), additions to the
PR body. The Lead applies them in SKILL.md § 10.

## Never
Commands agents must not run (full suite, anything that needs docker or a
live database, destructive setup scripts), each with the reason.

## Gotchas
Failures with a known cause and fix (a missing `.env`, a missing build of a
shared package, a slow test file).
```

Keep a profile short and factual. Every command in it has been checked to
exist in the repo on the date in `updated`.

## Workspace profiles

Some sessions start in a folder that is not a repository but holds several
(`~/src/weride-go` holds `weride-api` and `weride-ui`). A workspace profile
tells the Lead which repo a ticket belongs to (SKILL.md § 0 step 1). It
lives in the same folder, with `workspace` instead of `remote`:

```markdown
---
name: <folder name>
workspace: ~/src/<folder>        # the session folder; ~ is allowed
repos: [<profile name>, ...]     # the repo profiles of the repos it holds
updated: YYYY-MM-DD
---

# <folder> (workspace)

The repos it holds, each with its folder, remote and profile.

## Picking the repo
How to tell from a ticket which repo it belongs to (a ticket property, the
acceptance criteria).

## Full-stack tickets
How a ticket that needs more than one repo runs: order, run directories,
how one repo consumes another's unmerged change.

## Conventions
As in a repo profile; applies to every repo it holds unless that repo's
profile says otherwise.

## Gotchas
```

The Lead reads the workspace profile and the chosen repo's profile, and
records both in `run.json`.

## PR gates

What a PR in a repo needs before it merges: the bots that review it, the
human approvals, the CI checks. The PR watcher reads them from
`~/.team-lead/repos/<repo>.gates.json`, one file per repository whatever its `paths`
profiles, matched by `remote` like a profile.
`~/.claude/skills/team-lead/scripts/pr-gates.py <PR URL> --summary` scores
a PR against them. Without a file: every check on the PR's latest commit,
and one human approval.

```json
{
  "remote": "github.com/<owner>/<repo>",
  "updated": "YYYY-MM-DD",
  "gates": [
    {"id": "ci", "kind": "checks", "required": ["<check or status name>"],
     "details": {"url_pattern": "<regex, group 1 the run id>", "command": "<cli> {id}", "retry": "<cli> {id}"}},
    {"id": "human", "kind": "human", "min_approvals": 1,
     "ignore_authors": ["<login glob>"], "ignore_body_markers": ["<text a bot review carries>"]}
  ]
}
```

| `kind` | Reads | Fails on |
|---|---|---|
| `checks` | the named check runs and commit statuses, or every one with `"required": "all"` | any failed, cancelled or timed-out one |
| `human` | reviews from people: not bots, not the PR's author or the watcher's user, not `ignore_authors`, not a body with an `ignore_body_markers` text | a standing "changes requested", or a person's unresolved thread or comment that we have not answered last |
| `reef` | the `check` run, and the newest verdict comment by `authors` whose `reef-head-sha` is the head | a conclusion outside `pass_conclusions`, a finding not in an optional fold, or an unanswered Reef thread |
| `visual-qa` | the `check` run and the newest `visual-qa-report:1` comment by `authors` for the head; `skip_labels` pass it | any `fail` or `blocked` case not waived by an `@qa` `waive:` line; `max_blocked` caps how many blocked cases a round may waive |

A gate with nothing on a commit younger than `start_grace_minutes` (15 by
default) counts as running: bots and CI take a moment to start.

Three optional fields drive the watcher (`pr-watch.md`): `request` on a
gate, the comment that asks its bot to review a commit nobody asked it to
(`@qa done`); `max_auto_rounds` (3), how many rounds the watcher starts on
its own before it asks; and `merge`, the command that turns on auto-merge
once every gate passes (default `gh pr merge {pr} --auto --squash`).

Two more decide when the watcher asks for a human review in Slack:
`ask_review_after`, the gate ids that must be far enough along first (every
gate but the human one by default), and `review_risks` on a `reef` gate, the
Reef risk levels that count as far enough even with findings (`["low"]`).
A `reef` gate is far enough when it passes, its risk is in `review_risks`,
or Reef approved the commit; a `visual-qa` gate when no case failed and at
most `max_blocked` are blocked, waived or not; any other gate when it
passes.

## Creating or refreshing a profile

Run by `/team-lead --configure-repo [path]`. See the team-lead skill, section
*Configure a repo*.

Sources, most trusted first:

1. What the merge gate runs: CI config (`.github/workflows/`, `.rwx/`,
   `.circleci/`, `.buildkite/`), filtered to the jobs that cover the area.
2. What the repo tells contributors: `CLAUDE.md`/`AGENTS.md` at the root and
   in the area, `.claude/rules/`, `CONTRIBUTING.md`, the README.
3. What the repo runs per file: lint-staged config, pre-commit hooks,
   "PR ready" scripts.
4. The package scripts (`package.json`, `Makefile`, `justfile`,
   `pyproject.toml`, `Rakefile`) at the root, the area and a few
   representative packages of each kind.
5. Test runner and lint/format configs, to learn how to scope each command
   to single files.

Read from `origin/<default>` (`git show origin/<default>:<path>`), not the
working tree: the main checkout may sit on an unrelated branch.
