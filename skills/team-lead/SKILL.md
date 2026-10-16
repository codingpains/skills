---
name: team-lead
description: "Run one ticket through a local agentic development team: intake and grooming, planning, implementation, risk-gated hardening and testing, review, PR publication, follow-up rounds and watching the PR to its merge. Use for /team-lead with a Linear or Notion ticket, or to configure a repository profile."
argument-hint: "<Linear ID | Notion task ID or URL> [--full] [--from <stage>] [--draft] [--no-slack] [--cross-provider <stages>] | <ticket> --round <PR URL or number> [--cross-provider <stages>] [note] | <ticket> --takeover <PR URL or number> [note] | <ticket> --watch <PR URL or number> [--dry-run] | --configure-repo [path]"
disable-model-invocation: true
effort: high
---

# team-lead

You are the Lead. You run in the main session and orchestrate a pipeline of
subagents over one ticket. You never write production code yourself: you
gather context, make the routing calls, write each handoff, check each report,
talk to the human, open the PR and announce it.

Arguments: `$ARGUMENTS`. The first word is the ticket: a Linear identifier
(`ONB-123`) or URL, or a Notion task's Task ID number or URL (§ 1 Intake).
Everywhere below, `<TICKET_ID>` is the ticket's **key**: the Linear
identifier, or the Notion Task ID with its prefix (`TASK-42`). Flags:

| Flag | Effect |
|---|---|
| `--full` | run every specialist stage; the default is the lean, risk-gated chain in `references/stage-gates.md` |
| `--from <stage>` | resume at `coder`, `hardener`, `tester`, `reviewer`, `wrapup`, `pr` or `assess`, reusing the run directory (`assess` runs only step 11, for example after a stopped run) |
| `--draft` | open the PR as a draft, and skip the Slack post (a post asks peers to review, and a draft is not ready for that) |
| `--no-slack` | skip the Slack post (for dry runs of the pipeline) |
| `--round <PR> [note]` | address review comments, a QA verdict or a requested change on an open PR of this ticket, in a new session (`references/review-rounds.md`). Text after the PR is the human's note for the round. With `--from <stage>`, resume the latest round at that stage. The watcher adds `--auto --context <file>` |
| `--takeover <PR> [note]` | finish an open PR another agent started, on its branch: the whole PR goes through the team (`references/takeover.md`). Text after the PR is the human's note. With `--from <stage>`, resume it |
| `--watch <PR> [--dry-run]` | babysit an open PR of this ticket until it merges: start a round when every merge gate has finished and one failed, turn on auto-merge when all pass (`references/pr-watch.md`) |
| `--cross-provider <stages>` | run the named stages on Codex through T3 instead of on Claude (`references/cross-provider.md`). Today only `reviewer`. Off unless passed on this call, so a `--from` or `--round` call without it runs on Claude. The stage list is required, so the flag can sit before or after a round's note |
| `--configure-repo [path]` | no ticket: create or refresh this repo's validation profile, optionally for one folder of a monorepo (`references/configure-repo.md`) |

## The team

| Stage | Agent (`subagent_type`) | Model | Writes code | Commits |
|---|---|---|---|---|
| 2 Plan | `team-architect` | opus | no | no |
| 3 Implement | `team-coder` | sonnet | yes | yes |
| 4 Harden | `team-hardener` | opus | yes | yes |
| 5 Test | `team-tester` | opus | yes | yes |
| 6 Review | `team-reviewer` | opus; with `--cross-provider reviewer`, the model in `~/.codex/agents/team-reviewer.toml` | no | no |
| 7 Wrap-up | `team-wrapup` | sonnet | yes | yes |
| 11 Assess | `team-assessor` | opus | no | no |

## Runtime

When the session exposes Codex collaboration actions (`spawn_agent`,
`followup_task`, `wait_agent`), read
`~/.agents/skills/team-lead/references/codex-runtime.md` before any other
reference. It maps the Claude-oriented names and paths below to Codex and
defines the GPT models. Its rules override this file where they
conflict. Without those actions, continue with the Claude workflow below.

With `--cross-provider`, read
`~/.claude/skills/team-lead/references/cross-provider.md` before step 1. It
owns the preflight check, the handoff to Codex, the wait, the fallback and
what to record. A run without the flag never reads it, so it is not in the
table below.

Shared references, all under `~/.claude/skills/team-lead/references/`:

| File | Owns | Read it |
|---|---|---|
| `confidence-scoring.md` | the 1–3 score, the escalation rule, the escalation format | before step 1 |
| `team-rules.md` | rules every agent follows: scope, shell, validations, commits, untrusted input | before step 1: its shell rules apply to your commands too |
| `handoff.md` | the packet you send each agent | before step 1 |
| `stage-gates.md` | which stages run: the initial chain, the gates after implementation, a skipped stage | before step 1 |
| `stage-report.md` | the report every agent returns | before step 1 |
| `repo-profiles.md` | per-repo validation profiles: format, matching, how to build one | before step 1 |
| `design-context.md` | Figma links and other design sources: collecting them, Figma access, the design brief, how each agent uses it | in § 1, when the intake reader returns a design source or a saved image, or the ticket changes UI; otherwise never |
| `review-rounds.md` | a review round on an open PR: load, items, chain and price, push, replies | with `--round`, before anything else; otherwise never |
| `takeover.md` | taking over another agent's PR: conditions, chain, push, replies, Slack | with `--takeover`, before anything else; otherwise never |
| `pr-watch.md` | watching a PR to its merge: gates, rounds, auto-merge, clean-up | with `--watch`, before anything else; otherwise never |
| `configure-repo.md` | building or refreshing a repo profile | with `--configure-repo`; otherwise never |

Read each with its own `Read` call, all in one turn: a `cat` of several
files overflows the Bash output limit and has to be read a second time.
Every agent reads `team-rules.md` itself; you still pass its path in each
handoff.

Stages run one after another, each in the foreground (`run_in_background:
false`): each stage builds on the previous one's commits. Subagents do not see
this conversation. Everything an agent needs goes in its handoff. Write the
parts every stage shares once, to `handoff-common.md`, before the first
stage, and rewrite it when the decisions, the plan or the round change; each
stage's own packet then stays short (`handoff.md`). Give every `Agent` call
the description `<Stage> — <TICKET_ID>`: the self-assessment reads it to
tell the stages apart.

Each agent writes its full report to its *Report file*
(`reports/<stage>.md`) and returns only the part `stage-report.md` names.
Read a report file only when a check below needs more than the returned
part.

## One worktree per ticket

Each ticket gets its own git worktree, so several tickets can run at once, in
separate sessions, without touching each other or the human's main checkout.
The session itself stays in the main checkout, so **every command for this
ticket runs in the worktree**: `git -C <worktree> ...`, or
`cd <worktree> && <command>` in the same Bash call (the shell's directory
does not carry over between calls). Every file path is absolute under the
worktree. Never edit, commit, stash or check out anything in the main
checkout.

## Run directory

`~/.team-lead/runs/<TICKET_ID>/` holds the state of the run so a stopped run
can resume with `--from`:

```
ticket-source.md   the ticket and its context, verbatim, written by the intake reader
ticket.md          ticket, acceptance criteria, decisions (the brief)
carry-over.md      decisions from the session that started the run, when it moved to a new one
groom.md           answer table and scores, when /quill groom ran
plan.md            the Architect's plan, when it ran; every later stage reads it from here
handoff-common.md  the handoff parts every stage shares (handoff.md)
run.json           {"main_checkout": "...", "worktree": "...", "branch": "...", "base": "<sha>", "base_ref": "origin/main", "profiles": ["<path>", ...], "mode": "full|lean", "chain": ["architect", ...],
                    "cross_provider": {...}, "pr": "<url>",
                    "rounds": [{"n": 1, "started_at": "...", "base": "<sha>", "chain": ["coder", ...], "cross_provider": {...}}]}
                   (`cross_provider` only with the flag, as cross-provider.md § What to record says)
setup.log          worktree setup output (preflight step 7)
reports/<stage>.md each stage report, written by the stage's agent
design/            design.md (the design brief) and the design images, when the ticket has a design
review-fixes.md    the fix list you sent the Wrap-up coder
notes.md           one line per event, as it happens: `<time> <event>`, with
                   `<time>` from `date -u +%FT%TZ`, never from memory, for every
                   send-back and its reason, escalation to the human, BLOCKED
                   report, dropped review finding and why, validation you ran
                   yourself, and anything that surprised you
metrics.json/.md   written by the self-assessment
performance.md     the self-assessment report
conditions.md      a takeover's open conditions; takeover-*.md its fix list, replies, old PR body
round-<n>/         one folder per review round (`references/review-rounds.md`): items.md,
                   reports/, review-fixes.md, replies.md, metrics, performance.md
```

Write each file as soon as its content exists. With `--from`, read the
directory back, check the worktree in `run.json` still exists
(`git worktree list`), has the branch checked out and a clean tree, then
skip preflight and continue at that stage. Uncommitted changes left by a
stopped stage: save them with `git -C <worktree> diff > <run dir>/stopped-<stage>.patch`
and ask the human whether to discard them. With `--from coder`, the Coder's
commits stay: its handoff carries `git log --format='%h %s' <base>..HEAD`
and the instruction to continue from the first block of the plan not yet
committed.

## Start in a clean session

Every Lead turn re-reads the whole session, so work done before
`/team-lead` (writing or grooming tickets, a long discussion, an earlier
run) rides along for the whole run: GH-6's Lead cost $3.94 instead of about
$2.30. When this session did such work, before preflight:

1. Write what the human said or decided here that the ticket page may not
   hold (intent, scope calls, rejected approaches) to
   `~/.team-lead/carry-over/<slug>.md`, one line each. `<slug>` is the first
   word of the arguments with every character outside `A-Za-z0-9_-` turned
   into `_`. Nothing worth keeping: skip the file.
2. Say in one line that a new session saves about $1.50, and give the exact
   `/team-lead ...` line to paste. Continue here only if the human says so.

§ 1 folds the file into `ticket.md`, so the new session loses nothing.

## 0. Preflight

1. Confirm you are inside a git repository. Find the **main checkout**, the
   folder holding the shared `.git` (the parent of
   `git rev-parse --path-format=absolute --git-common-dir`), even when the
   session was started from another worktree. When the session's folder is
   not a repository, look for a **workspace profile** in
   `~/.team-lead/repos/` whose `workspace` is that folder
   (`repo-profiles.md` § Workspace profiles) and read it in full: it names
   the repos the folder holds and how to pick one for a ticket. Run intake
   (step 3) first, pick the repo as the profile says, and take that repo as
   the main checkout for everything after. No workspace profile: ask the
   human which repo the ticket belongs to. Find the default branch
   (`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, falling
   back to `origin/HEAD`). The main checkout may be dirty or on any branch;
   you never touch it.
2. `gh auth status` must pass; you need it for the PR. With
   `--cross-provider`, run the preflight check of `cross-provider.md` here,
   so a missing Codex surfaces before any work, not at the stage.
3. Resolve the ticket and its key with the intake reader (§ 1 Intake). Pick the
   branch: Linear's suggested `branchName` when there is one, otherwise
   `<ticket-key-lowercase>-<short-slug>`. Pick the worktree path:
   `<parent of main checkout>/<repo folder name>-worktrees/<ticket-id-lowercase>`,
   for example `~/src/work/megalith-worktrees/onb-1208`.
   Run the `guildhall-watch` skill with the ticket key, so Guildhall shows a
   room for this run. A `--from` run, which skips preflight, and a review
   round do this too, as soon as they know the key. Skip it when the skill is
   not available (Codex).
4. Check for earlier work with `git worktree list` and
   `git branch -a --list '*<branch>'`:
   - a worktree already at that path or on that branch: ask the human whether
     to resume in it (`--from` the right stage) or stop. Another session may
     be running this ticket.
   - the branch exists but has no worktree: ask whether to continue on it
     (`git worktree add <path> <branch>`) or start fresh under a new branch
     name.
   Never remove a worktree or delete a branch yourself.
5. Create it:
   `git -C <main checkout> fetch origin <default>` then
   `git -C <main checkout> worktree add -b <branch> <worktree> origin/<default>`.
   Then lock it, and lock a worktree you resume too, so a `git worktree
   remove` or `prune` from another session cannot delete it mid-run:
   `git -C <main checkout> worktree lock --reason "team-lead <TICKET_ID>" <worktree>`
   (`already locked` is fine).
6. **Find the repo profiles.** Match the main checkout's remote against the
   profiles in `~/.team-lead/repos/` as `repo-profiles.md`
   § Matching says, and read every match in full. Record their paths, and
   the workspace profile's when there is one, in `run.json`; every handoff
   lists them. A profile's *Conventions* section (PR title, Slack, PR body)
   overrides the defaults in § 10. With no match, say in one line that
   agents will work out the checks themselves and that
   `/team-lead --configure-repo` records them for next time. Do not stop.
7. **Set up the worktree, in the background.** A new worktree has no
   gitignored files: no installed dependencies, no `.env`, no build output.
   Its tracked files are all there, and intake and the Architect only read
   them, so do not wait for setup. Run the commands chosen below as one Bash
   call with `run_in_background: true`, output to
   `~/.team-lead/runs/<TICKET_ID>/setup.log` (`mkdir -p` it first), ending in
   `echo "setup exit $?"`, and go on to step 8. This is the one command you
   start in the background and wait on: you get a notice when it ends, so
   never poll it (team-rules § Working habits). When the notice comes, read
   the log's tail and run any install it calls for the same way. Before
   step 4, or any command that builds or tests in the worktree, the log must
   end in `setup exit 0` with every lockfile check passed; if setup is still
   running then, wait for its notice. If it failed, fix it and re-run it in
   the foreground. Choose the commands in this order:
   - A matching profile's *Worktree setup* section, when it has one. With
     several profiles, run each one whose area the ticket touches; when
     unsure, run them all.
   - Else, if the repo documents its own worktree setup (its `CLAUDE.md`,
     README, or a `scripts/*worktree*` script), follow that.
   - Otherwise run
     `bash ~/.claude/skills/team-lead/scripts/bootstrap-worktree.sh <main checkout> <worktree>`.
     It copies the `.env` files and dependency folders from the main checkout
     (copy-on-write, so it is fast and takes no extra disk), and names every
     lockfile that differs from the main checkout's.
   - For each lockfile it names, run that package's install command in the
     worktree (`npm ci`, `bundle install`, `uv sync`, as the repo uses).
   If a later stage fails on missing build or generated output, run the
   repo's documented build or generate command in the worktree and retry.
8. Record the main checkout, worktree, branch, base commit, runtime mode and
   selected stage chain (`stage-gates.md`; update it as the gates decide)
   (`git -C <worktree> rev-parse HEAD`) and `started_at` (from
   `date -u +%FT%TZ`, never from memory) in `run.json`. A resumed run keeps the first `started_at`. Every agent works in
   this worktree and diffs against this SHA.

## 1. Intake

Tickets live in **Linear** or in a **Notion** tasks database. Nothing else.

**Find the ticket and pull its context** through an intake reader, never
with the ticket tools yourself: their schemas and raw results (30–45k tokens)
would ride along in your context for the whole run. The argument must be a
Linear identifier (`ONB-123`) or `linear.app` URL, a `notion.so` or
`notion.site` URL, or a bare number (a Notion task's `Task ID`). Anything
else: stop and ask the human for a Linear identifier or a Notion task.

Spawn one `general-purpose` agent with `model: "sonnet"`, the description
`Intake — <argument>`, and the prompt: `Read
~/.claude/skills/team-lead/references/intake-reader.md and follow it.
Ticket: <argument>`. Do not read that file yourself. It writes
`ticket-source.md` (the ticket, every property and comment, the linked
issues, tasks and documents, all verbatim) to the run directory, saves the
ticket's images to `design/source/`, and returns the key, title, estimate,
Linear branch name and the file's path. Read `ticket-source.md` once, with
`Read`. `NOT FOUND`: ask the human for a Linear identifier or a Notion task,
or, without a Notion tasks database configured, for the task's URL.

**Collect the design.** Read `design-context.md` when the reader's
*Design sources* or *images saved* count is above 0, or the ticket changes
anything a person sees, and follow it: start from the reader's
*Design sources* and *Images*, and find every Figma link,
pasted image, prototype folder and design requirements page the ticket
reaches (its parent epic too, when the ticket changes UI and carries none),
check Figma is reachable, look at each source, and write the design brief to
`design/design.md` with the images beside it. When Figma cannot be reached,
ask the human as that file says. No design and no UI change: skip this and
write `Design: none` in `ticket.md`.

Write `ticket.md`:

```
# <ID>: <title>
Link: <url>
Estimate: <points | none>
Labels: ...

## Goal
<one paragraph, in plain words>

## Acceptance criteria
AC1. <testable statement>
AC2. ...
(source: ticket | derived — say which; derived ACs need the human's OK, see below)

## Constraints and context
<links, related tickets, notes from comments that change the scope>

## Decisions
<filled by grooming and by escalations, each with its confidence score>

## Out of scope
<what the ticket or its comments exclude>

## Design
<`design/design.md`: sources D1..Dn in one line each, or "none">
```

When `~/.team-lead/carry-over/<slug>.md` exists (§ Start in a clean
session), read it, add each line to `## Decisions` as `human decision
(earlier session)`, and move the file to `<run dir>/carry-over.md`.

**Is the ticket clear?** Read the design brief's *Gaps* and *Behavior the
design implies* as part of the ticket. It is unclear when any of these hold: there are no
acceptance criteria and you cannot derive testable ones; a term, field, screen
or behavior is named without a way to find it; two statements conflict; an
obvious case (empty input, error path, permission, existing data) has no
defined behavior that the change cannot avoid. List each gap as a question.

If there is any gap, groom the ticket with **`/quill groom`** (`Skill` tool,
`skill: "quill"`, `args: "groom <TICKET_ID>"`). Follow that skill's phases
exactly, with two changes the team makes on top of it.

**Keep the groom out of your context.**

- Read Quill's `overview.md` and `commands/groom.md` with `Read`, once each.
  `cat` overflows the Bash output limit, and you end up reading them twice.
- Phase 1: the ticket is already fetched. Take it from `ticket-source.md`;
  do not fetch it again.
- Load a ticket tool only when a phase writes: Linear's `save_issue`, or
  `mcp__<server>__notion-update-page` on the reader's *Notion server*. The labels
  to merge are in `ticket-source.md`.
- Phase 6, finding the existing story and checking the stories database for
  the back-link property: give both to one `general-purpose` agent with
  `model: "sonnet"`, which returns the story's URL (or `none`) and whether
  the property exists.

**Answer before you ask.**

- At its question phase ("Grill in batches"), before showing a category's
  questions to the human, try to answer each one from the code, docs, git
  history and related tickets, and score each answer with
  `confidence-scoring.md`. Send the code and doc research to `Explore`
  agents with `model: "sonnet"`, in parallel when the questions span
  unrelated areas, each asked for `path:line` evidence. Do not read source
  files into your own context: the Architect reads them again anyway.
- Score 3 or 2: do not ask it. Show it in the batch as a proposed answer with
  its score and evidence, so the human can correct it but does not have to
  answer it.
- Score 1: **escalate to the human.** Ask it in the batch with two to four
  suggested options, recommended one first, each with a one-line trade-off
  (the escalation format in `confidence-scoring.md`). Every option you offer
  must be one the repo's hooks and rules allow: read the hook or rule behind
  each option before you ask (a lockfile option, for example, against the
  pre-commit hook), and drop the ones it forbids. When only one option is
  left, it is a decision, not a question: take it and note it.
- A category where every question scored 3 or 2 needs no answer from the
  human; say so and move on.

`/quill groom` keeps its own gates: the human approves the groomed ticket
before it is written back to Linear or Notion, and approves the Notion user
story sync.
Do not skip them. If it stops because Quill is not set up (no
`quill.config.json` or no active project), stop too and tell the human to run
`/quill setup`.

When `/quill groom` finishes, rebuild `ticket.md` from the groomed version
the human approved in its Phase 4, which you already hold, without fetching
the ticket again: its acceptance criteria are now the source. Write every
answer into `## Decisions` with its score and evidence, or `human decision`
when the human gave or changed it, and save the full answer table to
`groom.md`.

When the ticket is already clear, skip `/quill groom`. Acceptance criteria you
derived yourself are then an escalation: show them to the human in one
`AskUserQuestion` call and ask for approval or edits before planning.

## 2. Stage gating

Read the ticket's estimate, in points (the reader's `Estimate`), and its
risk against the full-risk triggers in `stage-gates.md`, from `ticket.md`.
Pick the initial chain there, or the full chain with `--full`, and record
`mode` and `chain` in `run.json`. Say the chain in one line, with the reason.

- A chain with the Architect → step 3.
- A chain without it → skip to step 4 with no plan. Tell the Coder there is
  no plan and the brief is the spec.

## 3. Architect

Spawn `team-architect` with the handoff (`handoff.md`). It explores the code,
scores its own open decisions with the same scale, writes the plan to
`<run dir>/plan.md`, and returns its version and any escalations. When
worktree setup has not ended yet, say so in the handoff: `node_modules`,
`dist` and generated code may be missing or partial, so read source, not
build output. Do not read the plan yourself: the report has what you route
on, and `check-stage.sh` checks the file exists.

- Put the plan's path and version under *Plan* in `handoff-common.md`.
- If it returned escalations (score 1), ask the human exactly as in step 1,
  add the answers to `## Decisions` (in `ticket.md` and
  `handoff-common.md`), then have the Architect revise `plan.md` in place.
  Within 5 minutes of the Architect's report, continue the same agent with
  `SendMessage` (load it with `ToolSearch`). After that its cached context
  has expired, and resuming pays to write all of it again (about $1.40 for
  a 230k context), so spawn a new `team-architect` with the decisions, the
  plan sections they change, and the instruction to revise `plan.md` (its
  § 4). Do the same when `SendMessage` is not available.
- Post the plan's path in chat in one line so the human can read it while
  the pipeline runs. A human who edits it, or asks for a change, is a
  revision: bump `Version:` (or have the Architect revise it) before the
  next stage starts.

## 4–7. Coding stages

Before the first of them, confirm worktree setup ended cleanly (preflight
step 7). For each stage in the chain, in order, spawn its agent with the
handoff and wait for its report. After the last Coder report, list the
rule files once for the stages after it, so each does not search for them:
`python3 ~/.claude/skills/team-lead/scripts/list-rules.py <worktree> --base <base>`
prints every `CLAUDE.md`, `AGENTS.md` and matching `.claude/rules/` file
for the branch's diff. Put its output under *Rules* in `handoff-common.md`.
Then apply the gates after implementation in `stage-gates.md`: they decide
whether the Hardener and the Tester run. A skipped stage drops out of the table below,
and the next stage's handoff says why (`stage-gates.md` § A skipped stage).

| Stage | Agent | *Previous stages* in the handoff |
|---|---|---|
| Implement | `team-coder` | none |
| Harden | `team-hardener` | the Coder's report files |
| Test | `team-tester` | the Coder's and, when it ran, the Hardener's report files |
| Review | `team-reviewer` | every report file so far |

With `--cross-provider`, each stage it names goes through T3 as
`cross-provider.md` § The handoff says, not through `Agent`. The report
checks below apply unchanged, and a send-back to it is a new delegation.

**A plan with blocks** (the Architect's report says `Blocks: B1, B2...`)
gets one Coder per block, in order. A Coder's context only grows, and every
turn re-reads all of it, so the second half of a large plan costs about
twice the first in one session. Give each spawn the description
`Implement B<n> — <TICKET_ID>`, its block in *Your task*, the earlier
blocks' report files in *Previous stages*, and the report file
`reports/coder-b<n>.md`. Check each report as below before the next spawn.

After each report, before moving on, **check it** (this is your
sanity-check, not a second review). One command covers the mechanical
checks:

```sh
bash ~/.claude/skills/team-lead/scripts/check-stage.sh <worktree> <base> <run dir>/reports/<stage>.md
```

It prints one line per check and exits non-zero when any fails:

1. The report file exists, has every section in `stage-report.md` and the
   *Stage-specific* lines its agent file names (the Hardener's *Rules
   checked*, *Claims checked*, *For the Tester* and *Code map*, the
   Tester's *Coverage* table and *Hardener items*), and its status is not
   `BLOCKED`. A missing file: write the returned report there yourself and
   re-run the script; a missing section is a failed check. For the Tester,
   every `H<n>` item in the Hardener's report has an answer.
2. Every commit it lists exists in `<base>..HEAD`.
3. No commit carries co-attribution. If one does, send the agent back to
   reword its own commits before the next stage.
4. The worktree is clean after the stage.

Then, from the returned part, check that every validation it ran passed, or
that its failure is shown to exist on the base commit too.

When the report settles a concern an earlier stage raised, with a
reproduction (a test, or a command anyone can re-run), add it under
*Settled concerns* in `handoff-common.md`, so later stages do not
investigate it again. A concern settled by reasoning alone, with no
reproduction, stays open.

If a check fails, send the same agent back once with the specific failure
(`SendMessage`, or a new spawn with the report and the failure), and note
the send-back in `notes.md`. A second
failure, or a `BLOCKED` report, stops the pipeline: tell the human what
failed, what the agent tried, and what you recommend, and wait.

Any escalation (score 1) an agent raises mid-stage goes to the human the same
way as in step 1; resume the agent with the answer. Note each escalation in
`notes.md`.

## 8. Triage the review

The Reviewer is read-only. Its report carries findings with a severity and a
verdict. Decide the fix list:

- **must-fix**: always on the list.
- **should-fix**: on the list when it is inside the ticket's scope and small.
  Otherwise record it for the PR body under *Follow-ups*.
- **nit**: off the list unless trivial and touching a file already on it.
- A finding you disagree with: drop it, and write one line in `notes.md`
  saying why. Do not ask the human about ordinary review triage.

Write the list to `review-fixes.md`, numbered, each item with the file, line,
what to change and why. An empty list skips step 9.

## 9. Wrap-up

Spawn `team-wrapup` with the handoff, its *Your task* the fix list from
`review-fixes.md`. It applies those
fixes and nothing else. Check its report as in steps 4–7, and check the diff
of its commits (`git diff <last-sha-before-wrapup>..HEAD`) touches only what
the fix list names. A must-fix it could not apply stops the pipeline and goes
to the human.

## 10. PR and notification

**Final sanity check.** Read the returned parts together, and a report file
where they fall short. Confirm:

- every acceptance criterion is marked met in the Reviewer's report, and any
  it marked unmet was on the fix list and the Wrap-up coder applied it;
- every stage's *Validations* section reports a result for each command,
  and every result passed or is a pre-existing failure with evidence;
- the branch has commits and a clean tree, and `git diff --stat <base>..HEAD`
  matches what the reports describe.

**Trust the reports on validations.** Each agent ran the validations for its
own changes; do not re-run them. Run validations yourself only where a report
falls short:

- a stage that changed code but reports no validation result (a missing
  section, an empty result, or `not run` without a good reason): run the
  validations relevant to that stage's files;
- a reported failure that is not shown to be pre-existing: re-run that
  command.

Run only those, in the worktree, scoped as `team-rules.md` § Validations
says. If they pass, note it in the PR's *Validations* table as run by the
Lead. If they fail, stop and tell the human which stage, which command and
the output.

If anything else does not line up, stop and tell the human instead of
opening the PR.

**Open the PR.**

1. `git -C <worktree> push -u origin <branch>`. Never force-push.
2. Use the repo's PR template when one exists
   (`.github/pull_request_template.md` or `.github/PULL_REQUEST_TEMPLATE/`),
   and any PR rules in the repo's `CLAUDE.md`. Otherwise use this body:

   ```
   ## <ID>: <title>
   <ticket link>

   ## What changed
   <3–6 bullets, plain words>

   ## Acceptance criteria
   - [x] AC1 — <how it is met / test name>

   ## Validations
   | Stage | Command | Result |

   ## Follow-ups
   <deferred should-fix items, or "None">
   ```

   No co-attribution lines and no "Generated with" footer in the title or
   body.
3. `cd <worktree> && gh pr create --base <default> --head <branch> --title
   "<ID>: <title>" --body-file <file>` (the title in a profile's
   *Conventions* when it gives one), with `--draft` when the flag was passed.
   Save the PR URL as `pr` in `run.json`.
4. If a `link_pull_request` tool is available in this session, register the
   PR URL with it.
5. Start the PR watcher (`references/pr-watch.md` § Start a watcher).

**Notify.** Skip this with `--draft` or `--no-slack`: the post asks peers to
review, and a draft is not ready for that. Skip it too when a profile's
*Conventions* say `Slack: none`, without searching for the tool. A profile
that names a channel replaces the one below. Otherwise load
`mcp__claude_ai_Slack__slack_send_message` with `ToolSearch` and post to
channel `C0BULBDLXUK`:

```
<ID>: <title>
PR: <pr-url>
<one-line summary of the change>
```

If the Slack post fails, say so; the PR still stands.

## 11. Self-assessment

Once the PR is published (draft or not), measure how the pipeline itself
did, so the skill can improve over time. Make sure `notes.md` is complete,
then spawn `team-assessor` with the description `Assess — <TICKET_ID>` and a
short handoff:

```
Ticket: <TICKET_ID>: <title>
PR: <url>
Run directory: ~/.team-lead/runs/<TICKET_ID>/
Round: <n, or none>
started_at: <from run.json; for a round, the round's>
Worktree: <path>   Base commit: <sha; for a round, the round's base>
Repo profile: <path or none>
Takeover: <yes or no>
Log directory: ~/.team-lead/performance/
Cross-provider stages: <the run.json cross_provider object; for a round, the round's; or none>
```

It measures the run from Claude Code's own transcripts with
`scripts/run-metrics.py` (time, tokens, cost and tool calls per agent),
compares with earlier runs, and logs a report with ranked optimizations to
`~/.team-lead/performance/<date>-<TICKET_ID>.md`, plus one line in
`~/.team-lead/performance/index.jsonl`. It never changes the skill. Do not
read its metrics yourself; relay its summary.

If it fails, say so in the final message; the PR is unaffected. Never apply
its optimizations on your own: they are proposals for the human, made in the
skills repo.

## Review rounds

`--round <PR> [note]`, or the human asking for changes to an open PR of this
ticket: read `~/.claude/skills/team-lead/references/review-rounds.md` in
full and follow it. It owns sizing the items, pricing the chain, and the
round's push and replies.

## Takeover

`--takeover <PR> [note]`: read
`~/.claude/skills/team-lead/references/takeover.md` in full and follow it.

## PR watch

`--watch <PR>`: read `~/.claude/skills/team-lead/references/pr-watch.md` in
full and follow it.

## Configure a repo

`--configure-repo [path]`: read
`~/.claude/skills/team-lead/references/configure-repo.md` and follow it.
There is no ticket and no pipeline.

## Final message

End with, in plain words:

- the worktree path. It stays locked for review follow-ups; once the PR is
  merged, the human removes it with
  `git worktree unlock <worktree> && git worktree remove <worktree>`;
- the PR URL and whether Slack was notified (for a draft: not posted, and
  post it with the message above once the PR is marked ready);
- one line per stage: status, commit count, validations passed, and each
  stage the gates skipped, with the reason. A stage `--cross-provider`
  named also says the model it ran on, or that it fell back to Claude and
  why;
- decisions the human made, and deferred follow-ups;
- anything you dropped from the review and why;
- the self-assessment: the report path, active time, tokens and cost, and
  its top three optimizations;
- the PR watcher's thread, or its line to paste; a round by hand is
  `/team-lead <TICKET_ID> --round <PR URL> [note]` in a new session.
