# Repo profiles

A repo profile tells every agent exactly which checks to run for a change in
one repository, or one part of a monorepo, and how to set up a worktree for
it. Without a profile, agents work the commands out from the repo each time
(`team-rules.md` § Validations). With one, they start from commands that are
already known to work.

Profiles live in `~/.claude/skills/team-lead/repos/<name>.md`. That folder is
a symlink into the skills git repo, so profiles are versioned with the skill.
They are never committed to the target repository.

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

## Never
Commands agents must not run (full suite, anything that needs docker or a
live database, destructive setup scripts), each with the reason.

## Gotchas
Failures with a known cause and fix (a missing `.env`, a missing build of a
shared package, a slow test file).
```

Keep a profile short and factual. Every command in it has been checked to
exist in the repo on the date in `updated`.

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
