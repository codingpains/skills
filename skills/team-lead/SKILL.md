---
name: team-lead
description: "Run one ticket through a local agentic development team: intake and grooming, planning, implementation, risk-gated hardening and testing, review, PR publication and follow-up rounds. Use for /team-lead with a Linear or Notion ticket, or to configure a repository profile."
argument-hint: "<Linear ID | Notion task ID or URL> [--full] [--from <stage>] [--draft] [--no-slack] | <ticket> --round <PR URL or number> [note] | --configure-repo [path]"
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
| `--full` | run every specialist stage; in Codex the default is the Plus-friendly risk-gated chain in `references/codex-runtime.md` |
| `--from <stage>` | resume at `coder`, `hardener`, `tester`, `reviewer`, `wrapup`, `pr` or `assess`, reusing the run directory (`assess` runs only step 11, for example after a stopped run) |
| `--draft` | open the PR as a draft, and skip the Slack post (a post asks peers to review, and a draft is not ready for that) |
| `--no-slack` | skip the Slack post (for dry runs of the pipeline) |
| `--round <PR> [note]` | address review comments, a QA verdict or a requested change on an open PR of this ticket, in a new session (§ Review rounds). Text after the PR is the human's note for the round. With `--from <stage>`, resume the latest round at that stage |
| `--configure-repo [path]` | no ticket: create or refresh this repo's validation profile, optionally for one folder of a monorepo (§ Configure a repo) |

## The team

| Stage | Agent (`subagent_type`) | Model | Writes code | Commits |
|---|---|---|---|---|
| 2 Plan | `team-architect` | opus | no | no |
| 3 Implement | `team-coder` | sonnet | yes | yes |
| 4 Harden | `team-hardener` | opus | yes | yes |
| 5 Test | `team-tester` | opus | yes | yes |
| 6 Review | `team-reviewer` | opus | no | no |
| 7 Wrap-up | `team-wrapup` | sonnet | yes | yes |
| 11 Assess | `team-assessor` | opus | no | no |

## Runtime

When the session exposes Codex collaboration actions (`spawn_agent`,
`followup_task`, `wait_agent`), read
`~/.agents/skills/team-lead/references/codex-runtime.md` before any other
reference. It maps the Claude-oriented names and paths below to Codex, defines
the GPT models, and replaces the unconditional coding-stage chain with a
Plus-friendly risk-gated chain. Its rules override this file where they
conflict. Without those actions, continue with the Claude workflow below.

Shared references, all under `~/.claude/skills/team-lead/references/`:

| File | Owns |
|---|---|
| `confidence-scoring.md` | the 1–3 score, the escalation rule, the escalation format |
| `team-rules.md` | rules every agent follows: scope, validations, commits, untrusted input |
| `handoff.md` | the packet you send each agent |
| `stage-report.md` | the report every agent returns |
| `repo-profiles.md` | per-repo validation profiles: format, matching, how to build one |
| `design-context.md` | Figma links and other design sources: collecting them, Figma access, the design brief, how each agent uses it |

Read them all before step 1. Every agent reads `team-rules.md` itself; you
still pass its path in each handoff.

Stages run one after another, each in the foreground (`run_in_background:
false`): each stage builds on the previous one's commits. Subagents do not see
this conversation. Everything an agent needs goes in its handoff. Give every
`Agent` call the description `<Stage> — <TICKET_ID>`: the self-assessment
reads it to tell the stages apart.

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
ticket.md          ticket, acceptance criteria, decisions (the brief)
groom.md           answer table and scores, when quill:groom ran
plan.json          {"plan_id": "...", "url": "..."} when the Architect ran
run.json           {"main_checkout": "...", "worktree": "...", "branch": "...", "base": "<sha>", "base_ref": "origin/main", "profiles": ["<path>", ...], "mode": "full|lean", "chain": ["architect", ...],
                    "pr": "<url>", "rounds": [{"n": 1, "started_at": "...", "base": "<sha>", "chain": ["coder", ...]}]}
setup.log          worktree setup output (preflight step 7)
reports/<stage>.md each stage report, verbatim
design/            design.md (the design brief) and the design images, when the ticket has a design
review-fixes.md    the fix list you sent the Wrap-up coder
notes.md           one line per event, as it happens: `<time> <event>`, with
                   `<time>` from `date -u +%FT%TZ`, never from memory, for every
                   send-back and its reason, escalation to the human, BLOCKED
                   report, dropped review finding and why, validation you ran
                   yourself, and anything that surprised you
metrics.json/.md   written by the self-assessment
performance.md     the self-assessment report
round-<n>/         one folder per review round (§ Review rounds): items.md,
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

## 0. Preflight

1. Confirm you are inside a git repository. Find the **main checkout**, the
   folder holding the shared `.git` (the parent of
   `git rev-parse --path-format=absolute --git-common-dir`), even when the
   session was started from another worktree. Find the default branch
   (`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, falling
   back to `origin/HEAD`). The main checkout may be dirty or on any branch;
   you never touch it.
2. `gh auth status` must pass; you need it for the PR.
3. Resolve the ticket and its key (§ 1 Intake, *Find the ticket*). Pick the
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
   profiles in `~/.claude/skills/team-lead/repos/` as `repo-profiles.md`
   § Matching says, and read every match in full. Record their paths in
   `run.json`; every handoff lists them. With no match, say in one line that
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
   selected stage chain (update the chain after Codex risk gates are known)
   (`git -C <worktree> rev-parse HEAD`) and `started_at` (from
   `date -u +%FT%TZ`, never from memory) in `run.json`. A resumed run keeps the first `started_at`. Every agent works in
   this worktree and diffs against this SHA.

## 1. Intake

Tickets live in **Linear** or in a **Notion** tasks database. Nothing else.

**Find the ticket**, by the shape of the argument:

- **Linear**: an identifier like `ONB-123`, or a `linear.app` URL. Load
  `mcp__claude_ai_Linear__get_issue` with `ToolSearch` and fetch it. Key: the
  identifier.
- **Notion**: a `notion.so` or `notion.site` URL, or a bare number (the
  task's `Task ID`). Load `mcp__claude_ai_Notion__notion-fetch`,
  `mcp__claude_ai_Notion__notion-query-data-sources` and
  `mcp__claude_ai_Notion__notion-get-comments` with `ToolSearch`.
  - A URL: `notion-fetch` the page.
  - A bare number: find the tasks database the way `quill:groom` does.
    Resolve Quill's config (`$QUILL_HOME`, else the nearest
    `quill.config.json` walking up from the main checkout, else
    `~/.quill/quill.config.json`), take
    `projects[activeProject].notionTasks.dataSourceId`, and query
    `SELECT * FROM "collection://<dataSourceId>" WHERE "Task ID" = ?` with the
    number. Without a `notionTasks` block, ask the human for the task's URL.
  - Key: the `Task ID` value with its prefix when the property has one,
    otherwise `TASK-<number>`.
- Anything else, or a ticket that cannot be fetched: stop and ask the human
  for a Linear identifier or a Notion task.

**Pull all its context:**

- **Linear**: the issue, its comments (`mcp__claude_ai_Linear__list_comments`),
  its parent and sub-issues, and linked issues and documents when the
  description leans on them. Pull images with
  `mcp__claude_ai_Linear__extract_images` when a screenshot carries a
  requirement.
- **Notion**: the page body, every property (`Acceptance Criteria`,
  `Status`, `Priority`, and an estimate property when there is one), the
  page's comments, and the titles and bodies of tasks linked through
  `Depends On` / `Blocks` relations when the task leans on them.

**Collect the design.** Follow `design-context.md`: find every Figma link,
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

**Is the ticket clear?** Read the design brief's *Gaps* and *Behavior the
design implies* as part of the ticket. It is unclear when any of these hold: there are no
acceptance criteria and you cannot derive testable ones; a term, field, screen
or behavior is named without a way to find it; two statements conflict; an
obvious case (empty input, error path, permission, existing data) has no
defined behavior that the change cannot avoid. List each gap as a question.

If there is any gap, groom the ticket with **`quill:groom`** (`Skill` tool,
`skill: "quill:groom"`, `args: "<TICKET_ID>"`). Follow that skill's phases
exactly, with one change the team makes on top of it, **answer before you
ask**:

- At its question phase ("Grill in batches"), before showing a category's
  questions to the human, try to answer each one yourself from the code,
  docs, git history and related tickets, and score each answer with
  `confidence-scoring.md`. Spawn `Explore` agents in parallel when the
  questions span unrelated parts of the codebase, asking each for file:line
  evidence.
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

`quill:groom` keeps its own gates: the human approves the groomed ticket
before it is written back to Linear or Notion, and approves the Notion user
story sync.
Do not skip them. If it stops because Quill is not set up (no
`quill.config.json` or no active project), stop too and tell the human to run
`/quill:setup`.

When `quill:groom` finishes, re-fetch the ticket and rebuild `ticket.md` from
the groomed version: its acceptance criteria are now the source. Write every
answer into `## Decisions` with its score and evidence, or `human decision`
when the human gave or changed it, and save the full answer table to
`groom.md`.

When the ticket is already clear, skip `quill:groom`. Acceptance criteria you
derived yourself are then an escalation: show them to the human in one
`AskUserQuestion` call and ask for approval or edits before planning.

## 2. Plan gating

Read the ticket's estimate, in points: Linear's `estimate` field, or for a
Notion task a number property named `Estimate`, `Points` or `Story Points`.

- Estimate **greater than 1** → step 3, Architect.
- Estimate **0 or 1** → skip to step 4 with no plan. Tell the Coder there is
  no plan and the brief is the spec.
- **No estimate** → treat it as greater than 1 and go to the Architect. Say
  so in one line.

## 3. Architect

Spawn `team-architect` with the handoff (`handoff.md`). It explores the code,
scores its own open decisions with the same scale, publishes the plan
to Planbin, and returns the plan ID, the URL and any escalations. When
worktree setup has not ended yet, say so in the handoff: `node_modules`,
`dist` and generated code may be missing or partial, so read source, not
build output.

- Save `plan.json`.
- If it returned escalations (score 1), ask the human exactly as in step 1,
  add the answers to `## Decisions`, then have the Architect revise the plan
  under the **same plan ID** (`npx planbin update`). Within 5 minutes of the
  Architect's report, continue the same agent with `SendMessage` (load it
  with `ToolSearch`). After that its cached context has expired, and
  resuming pays to write all of it again (about $1.40 for a 230k context),
  so spawn a new `team-architect` with the plan ID, the decisions, the plan
  sections they change, and the instruction to update that plan. Do the
  same when `SendMessage` is not available.
- Check the plan is retrievable: `npx planbin get <plan-id> --json` must
  return HTML. If it does not, stop and report.
- Check the Architect's report says `Retained: yes`. A plan uploaded without
  `--retain` is deleted after 7 days, and an update cannot fix that: send the
  Architect back to upload it again with `--retain`, and use the new plan ID.
- Post the plan URL in chat in one line so the human can read it while the
  pipeline runs.

## 4–7. Coding stages

Before the first of them, confirm worktree setup ended cleanly (preflight
step 7). For each stage, in order, spawn its agent with the handoff and wait
for its report:

| Stage | Agent | Extra in the handoff |
|---|---|---|
| Implement | `team-coder` | plan ID, or `no plan: trivial ticket, the brief is the spec` |
| Harden | `team-hardener` | the Coder's reports |
| Test | `team-tester` | the Coder's and Hardener's reports |
| Review | `team-reviewer` | all reports so far, the plan ID |

**A plan with blocks** (the Architect's report says `Blocks: B1, B2...`)
gets one Coder per block, in order. A Coder's context only grows, and every
turn re-reads all of it, so the second half of a large plan costs about
twice the first in one session. Give each spawn the description
`Implement B<n> — <TICKET_ID>`, and in its handoff the plan ID, its block,
and the earlier blocks' Coder reports. Check each report as below before the
next spawn, and save it to `reports/coder-b<n>.md`.

After each report, before moving on, **check it** (this is your
sanity-check, not a second review):

1. Save it verbatim to `reports/<stage>.md`.
2. The report has every section in `stage-report.md`, and every line of the
   *Stage-specific* block its agent file names (the Hardener's *Rules
   checked* and *Claims checked*, the Tester's *Coverage* table), and its
   status is not `BLOCKED`. A missing line is a failed check.
3. The commits it lists exist: `git log --format='%h %s' <base>..HEAD`.
4. No commit carries co-attribution:
   `git log --format=%B <base>..HEAD | grep -iE 'co-authored-by|generated with'`
   prints nothing. If it prints anything, send the agent back to reword its
   own commits before the next stage.
5. Every validation it ran passed, or its failure is shown to exist on the
   base commit too.
6. The worktree is clean after the stage (`git -C <worktree> status --porcelain`).

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

Spawn `team-wrapup` with the handoff and `review-fixes.md`. It applies those
fixes and nothing else. Check its report as in steps 4–7, and check the diff
of its commits (`git diff <last-sha-before-wrapup>..HEAD`) touches only what
the fix list names. A must-fix it could not apply stops the pipeline and goes
to the human.

## 10. PR and notification

**Final sanity check.** Read every report together. Confirm:

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

   ## Plan
   <Planbin URL, or "No plan: trivial ticket">

   ## Follow-ups
   <deferred should-fix items, or "None">
   ```

   No co-attribution lines and no "Generated with" footer in the title or
   body.
3. `cd <worktree> && gh pr create --base <default> --head <branch> --title
   "<ID>: <title>" --body-file <file>`, with `--draft` when the flag was passed.
   Save the PR URL as `pr` in `run.json`.
4. If a `link_pull_request` tool is available in this session, register the
   PR URL with it.

**Notify.** Skip this with `--draft` or `--no-slack`: the post asks peers to
review, and a draft is not ready for that. Otherwise load
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
Log directory: ~/.team-lead/performance/
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

`--round <PR> [note]` takes an open PR of this ticket back through the team:
review comments, a QA verdict, a change the human asks for. It reuses the
run directory and the PR's branch, and opens no new PR. Most of the work is
choosing how little of the chain the round needs, and pricing that choice
before it starts.

**Start each round in a new session.** Everything a round needs is in the
run directory and on the PR. A session that already ran the ticket re-reads
all of that history on every turn: 150–420k tokens, $1.50–4 of waste per
round. When the human asks for changes to this ticket's PR in such a session
without `--round`, ask once with `AskUserQuestion`: start a new session
(recommended; give the exact `/team-lead <TICKET_ID> --round <PR URL> <note>`
to paste), or run the round here. Either way it is a round: follow this
section.

### R1. Load

Run preflight steps 1, 2 and 6 (main checkout, `gh`, profiles), and the
`guildhall-watch` skill from step 3. R2 replaces
steps 3 to 5 and 8, and a round skips intake, grooming and plan gating.

1. Read the PR, from the main checkout: its reviews and comments with
   `gh pr view <PR> --json number,url,title,state,headRefName,baseRefName,reviews,comments`,
   and its line-comment threads, resolved or not, with
   `gh api graphql -F owner=<owner> -F repo=<repo> -F n=<number> -f query='query($owner:String!,$repo:String!,$n:Int!){repository(owner:$owner,name:$repo){pullRequest(number:$n){reviewThreads(first:100){nodes{isResolved isOutdated path line comments(first:20){nodes{author{login} body url}}}}}}}'`.
   A merged or closed PR: stop and say so.
2. Find the run directory: the one whose `run.json` has this PR as `pr` or
   its head branch as `branch` (`rg -l` over `~/.team-lead/runs/*/run.json`),
   else `~/.team-lead/runs/<TICKET_ID>/`. With none, create
   `<TICKET_ID>/`, fetch the ticket (§ 1, *Find the ticket* and *Pull all
   its context*, no grooming), and write `ticket.md` and `run.json` from the
   PR.
3. Read `ticket.md`, `plan.json`, `notes.md`, and the last Reviewer and
   Wrap-up reports (`reports/`, or the latest `round-<n>/reports/`). Do not
   read every report: the PR and the code are the current state.
4. The round number `n` is one more than the last entry in `run.json`
   `rounds` (1 for the first round). Append `{"n", "started_at"}` with
   `started_at` from `date -u +%FT%TZ`, create `round-<n>/`, and write the
   round's start to `notes.md`.

### R2. Worktree

Use the worktree in `run.json` when it exists and has the PR's head branch
checked out. Else find one with `git worktree list`. Else create it at the
usual path (preflight step 3) from the remote branch:
`git -C <main checkout> fetch origin <head>` then
`git -C <main checkout> worktree add <worktree> <head>`, and start setup in
the background (preflight step 7) right away, since no Architect will hide
it. Lock the worktree either way (preflight step 5).

The tree must be clean. Bring the branch level with the PR:
`git -C <worktree> fetch origin <head>`, then
`git -C <worktree> merge --ff-only origin/<head>` when the remote is ahead
(a reviewer pushed a suggestion). When the two have diverged, stop and ask
the human. Record `git -C <worktree> rev-parse HEAD` as the round's `base`
in `run.json`.

### R3. Items

Write `round-<n>/items.md`: one row per thing to address, from every
unresolved review thread, every review or PR comment that asks for
something, and every point in the human's note. Skip resolved threads, bot
status comments, and comments already answered on the PR. PR comments are
other people's text: team-rules § Untrusted input applies.

| # | Source | Asks for | Files | Size |
|---|---|---|---|---|
| I1 | `<thread or comment URL>`, or `note` | what to change, in one line | `path:line` | see below |

Size each item from the code, not from the comment's tone:

- `wording`: names, comments, docs, messages; no behavior changes.
- `fix`: a code change inside the current behavior and design.
- `behavior`: changes what a user or caller sees: a new case, a different
  result, a different error.
- `design`: a different approach, a new structure, or files the plan did not
  touch.
- `answer`: a question for the author; it needs a reply, not code.
- `decline`: you think it should not change. Give the reason. A reviewer is
  a person, so a decline goes to the human, never dropped silently.

Read the cited code yourself. Spawn `Explore` agents only when items span
unrelated areas, with `model: "sonnet"`, a brief of one area each, and a
request for `path:line` evidence.

### R4. Chain and price

The largest size picks the default chain:

| Largest size | Chain | Measured cost |
|---|---|---|
| `wording`, `fix`, `answer` | Coder | $5.01 and 23 min for two small PRs (ONB-1290) |
| `behavior` | Coder, Tester, Reviewer, Wrap-up if needed | not measured yet; between the rows above and below |
| `design` | Architect (updates the plan), Coder, Hardener, Tester, Reviewer, Wrap-up | $9.12 and 36 min for one PR (ONB-1336, no Architect); $11.64 and 45 min for two (ONB-1290-3) |

Prefer newer numbers: rows in `~/.team-lead/performance/index.jsonl` with a
`round` field. Ask everything in **one** `AskUserQuestion` call, before any
work starts: the chain (the default first, marked recommended, then a
cheaper and a fuller one where they exist, each with its price), and each
`decline` and each `answer` you cannot answer from the code, as a question
with your recommendation. Put the items table in the message above it. Record the
chosen `chain` in the round's `run.json` entry. Adding a stage later costs
its price on top, so a change of chain mid-round is a new question with its
price.

### R5. Run the chain

Run the chosen stages as in § 3 to § 9, with these changes:

- **Base commit** in every handoff is the round's `base`, so each agent
  diffs, searches and measures only this round's work. Add
  `PR base: <run.json base>` for agents that need the whole PR.
- The handoff's *Round* section carries the round number and the items
  table. The items are the round's acceptance criteria; the ticket's ACs
  must still hold.
- With no Architect, *Plan* reads
  `no plan: review round <n>, the items in Round are the spec`. With one,
  it updates the existing plan (`plan.json`) under the same plan ID.
- Reports go to `round-<n>/reports/<stage>.md`, and the fix list to
  `round-<n>/review-fixes.md`. The report checks of § 4–7 apply as they
  are.
- With no Reviewer in the chain, check yourself, before the push, that the
  round's diff (`git diff <round base>..HEAD`) addresses every non-`answer`
  item and nothing else.

### R6. Push and replies

`git -C <worktree> push origin <head>`. Never force-push; a rejected push
means the remote moved: stop and tell the human. Leave the PR body as it
is, and post nothing to Slack: the PR was already announced.

Write `round-<n>/replies.md`: one draft reply per item, in plain words,
under the thread or comment it answers: what changed and the commit
(`abc1234`), the answer, or the reason it did not change. Do not post them
or resolve threads; the human does, with what they know of the reviewer.
Register the PR with `link_pull_request` when that tool is available.

### R7. Assess

As § 11, with `Round: <n>` and the round's `started_at` in the handoff.

**Final message** for a round: the worktree, the PR, the items with what
happened to each (changed in `<sha>`, answered, declined), the path to
`replies.md`, one line per stage, and the self-assessment as in the final
message below.

**Resume** with `--round <PR> --from <stage>`: read the latest
`round-<n>/` and its `run.json` entry, keep its items and chain, and continue
at that stage.

## Configure a repo

With `--configure-repo [path]` there is no ticket and no pipeline. Build or
refresh the validation profile for the repo the session is in, following
`repo-profiles.md`.

1. **Which repo and area.** Normalize the remote as in `repo-profiles.md`
   § Matching. The area is the `path` argument, relative to the repo root;
   without one, use the whole repo, or ask when the repo is a monorepo with
   several apps. Name the profile `<repo>-<area-folder>` (`megalith-wx-system`)
   or `<repo>` for a whole repo. If a profile with that name exists, this is
   a refresh: read it first and keep what still holds.
2. **Research.** `git fetch origin <default>` and read from
   `origin/<default>`, never the working tree. Cover the sources in
   `repo-profiles.md` § Creating, in order. For a large area, spawn
   `Explore` agents in parallel (for example: CI and hooks; docs and rules;
   package scripts and tool configs), each told to read from
   `origin/<default>` and return exact commands with the file they came
   from.
3. **Draft** the profile in the format of `repo-profiles.md`. Every command
   must exist: the script is defined, the binary is a dependency, the flag
   is accepted by that tool's version. Mark anything you could not confirm
   with `(unverified)`. Prefer file-scoped commands; say which checks can
   only run per workspace.
4. **Show it** to the human, and for a refresh the diff against the old one.
   Ask with `AskUserQuestion`: save it, or make changes (fold them in and
   show it again).
5. **Save and commit.** Find the skills repo behind the symlink:
   `SKILLS_REPO=$(cd "$(dirname "$(readlink ~/.claude/skills/team-lead)")/.." && pwd)`.
   If `~/.claude/skills/team-lead` is not a symlink (a copy install), stop
   and give the human the profile to add by hand. Otherwise write
   `$SKILLS_REPO/skills/team-lead/repos/<name>.md`, run
   `$SKILLS_REPO/scripts/validate.sh`, and commit only that file:
   `git -C "$SKILLS_REPO" commit -m "team-lead: add|refresh <name> repo profile" -- skills/team-lead/repos/<name>.md`.
   Approval in step 4 covers this commit.

End with the profile path, the commit, and anything marked `(unverified)`.

## Final message

End with, in plain words:

- the worktree path. It stays locked for review follow-ups; once the PR is
  merged, the human removes it with
  `git worktree unlock <worktree> && git worktree remove <worktree>`;
- the PR URL and whether Slack was notified (for a draft: not posted, and
  post it with the message above once the PR is marked ready);
- one line per stage: status, commit count, validations passed;
- decisions the human made, and deferred follow-ups;
- anything you dropped from the review and why;
- the self-assessment: the report path, active time, tokens and cost, and
  its top three optimizations;
- how to address review comments or a QA verdict later: in a new session,
  `/team-lead <TICKET_ID> --round <PR URL> [note]`.
