# skills

My Claude Code skills and agents, under version control. Edit here, commit,
and install into `~/.claude` with `./install.sh`.

## Layout

```
skills/<name>/SKILL.md     a skill (plus its references/ and scripts/)
agents/<name>.md           a subagent definition
install.sh                 install into ~/.claude (symlink by default)
scripts/validate.sh        frontmatter and reference checks (runs on commit and install)
.githooks/pre-commit       runs validate.sh
```

## Install

```sh
./install.sh              # symlink everything; edits in this repo are live
./install.sh --copy       # copy instead: a frozen snapshot, re-run to update
./install.sh --status     # what is installed, and how
./install.sh --uninstall  # remove only what this repo installed
./install.sh --force      # replace a same-named skill/agent not from this repo (backs it up)
```

With symlinks, editing an existing skill or agent needs no reinstall. Run
`./install.sh` again after **adding, renaming or deleting** one; it links the
new ones and prunes links whose source is gone. Start a new Claude Code
session to pick up new agents.

After cloning, turn on the commit check once:

```sh
git config core.hooksPath .githooks
```

## Making a change

1. Edit the files here (or ask Claude to, from this folder).
2. `scripts/validate.sh`
3. Commit.
4. `./install.sh` if you added, renamed or removed a skill or agent.

## What is here

### `/team-lead TICKET_ID` — a local development team

The Lead (a skill in the main session) runs one ticket through a pipeline of
subagents, then opens the PR and posts it to Slack channel `C0BULBDLXUK`.

```
Intake ──► unclear? ──► quill:groom (Lead answers from code, scored 1–3; score 1 → ask the human)
   │
   ▼
estimate > 1 point (or none)? ──► Architect (fable) ──► plan on Planbin
   │ no                                                     │
   ▼                                                        ▼
Coder (sonnet) ──► Hardener (opus) ──► Tester (opus) ──► Reviewer (opus)
                                                            │
                          Lead picks the fixes ◄────────────┘
                                   │
                                   ▼
                       Wrap-up coder (sonnet) ──► PR ──► Slack
```

| Piece | File | Model |
|---|---|---|
| Lead | `skills/team-lead/SKILL.md` | main session |
| Grooming | `quill:groom` (Quill plugin, not in this repo) | main session |
| Architect | `agents/team-architect.md` | fable |
| Coder | `agents/team-coder.md` | sonnet |
| Hardener | `agents/team-hardener.md` | opus |
| Tester | `agents/team-tester.md` | opus |
| Reviewer | `agents/team-reviewer.md` | opus |
| Wrap-up coder | `agents/team-wrapup.md` | sonnet |

Shared rules live in `skills/team-lead/references/`:
`confidence-scoring.md`, `team-rules.md` (scope, validations, commits),
`handoff.md` (what each agent receives), `stage-report.md` (what each agent
returns).

Each ticket runs in its own git worktree at
`<repo>-worktrees/<ticket-id>` next to the main clone, so several tickets can
run at once in separate sessions and your main checkout is never touched.
`skills/team-lead/scripts/bootstrap-worktree.sh` copies `.env` files and
dependency folders into a new worktree. Remove a worktree yourself once its PR
is merged: `git worktree remove <path>`.

Flags: `--from <stage>` resumes a stopped run from
`~/.team-lead/runs/<TICKET_ID>/`; `--draft` opens a draft PR and skips the
Slack post, so peers are not asked to review it; `--no-slack` skips the Slack
post for a ready PR.

**Needs:** `gh` logged in; the Quill plugin set up (`/quill:setup`) for
grooming; the Linear and Slack connectors authorized in Claude; the `planbin-cli` skill and `npx planbin login` done once. The
Hardener and Tester use the complexity, duplication and coverage scripts in
`~/.claude/agents/references/` when present, and fall back to standard tools
otherwise.
