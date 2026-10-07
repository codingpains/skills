# Handoff packet

Subagents see nothing from the main session but their prompt, so leave
nothing implicit. Fill every field; write `none` rather than dropping a
field.

The packet comes in two parts. What every stage shares lives in
`<run dir>/handoff-common.md`, written once before the first stage. Each
stage's prompt is a short packet that points at it. Retyping the shared part
into every prompt costs the Lead output and context on every transition.

## handoff-common.md

Write it before the first stage. Rewrite it when the decisions, the plan or
the round change: a stale shared file misleads every later stage.

```
# <TICKET_ID>: <title> — shared handoff

Read first: ~/.claude/skills/team-lead/references/team-rules.md
Report format: ~/.claude/skills/team-lead/references/stage-report.md

## Where
Worktree: <absolute path>   # all your work happens here; see team-rules § Scope
Branch: <branch> (checked out in the worktree)
Base commit: <sha>   # diff everything against this: git diff <sha>...HEAD (in a review round, the round's base)
Default branch: <name>
Repo profiles: <absolute paths, each with its `paths` scope, or "none: work the checks out yourself">
Run directory: ~/.team-lead/runs/<TICKET_ID>/  # the Lead's state; write here only your report file and what your agent file says

## Ticket
Link: <url>
Estimate: <points | none>

### Goal
<from ticket.md>

### Acceptance criteria
AC1. ...
AC2. ...

### Decisions
<from ticket.md, each with its score or "human decision">

### Out of scope
<from ticket.md>

## Design
<"none", or:
Brief: ~/.team-lead/runs/<TICKET_ID>/design/design.md (read it, and open every image it lists)
Figma: D1 <url> node <id>, ...   Figma tools: <mcp__plugin_quill_figma__ | mcp__claude_ai_Figma__ | none reachable>
How to use it: ~/.claude/skills/team-lead/references/design-context.md § How each agent uses it>

## Plan
<Planbin plan ID and URL; "none yet: you are the Architect";
"no plan: trivial ticket, the brief is the spec";
or "no plan: review round <n>, the items in Round are the spec">

## Round
<"none", or for a review round (SKILL.md § Review rounds):
Round: <n>   PR: <url>   PR base: <run.json base>   # Base commit above is the round's base
Items (the round's acceptance criteria; the ticket's ACs must still hold):
| # | Source | Asks for | Files | Size |
...the rows of round-<n>/items.md>
```

## Each stage's prompt

```
# <Stage> — <TICKET_ID>: <title>

Read ~/.team-lead/runs/<TICKET_ID>/handoff-common.md first: it holds the
worktree, the ticket, the design and the plan.

Report file: ~/.team-lead/runs/<TICKET_ID>/reports/<stage>.md
  (in a review round: round-<n>/reports/<stage>.md)

## Previous stages
<the earlier stages' report files, one path per line, the immediately
previous one first, or "none". Read the immediately previous one in full;
of the older ones, read Status, Commits, Validations and Concerns.>

## Your task
<the stage's task in one or two sentences, and only what is specific to this
stage: the block for a Coder, the Round rows it acts on, the numbered fix
list from review-fixes.md verbatim for the Wrap-up>
```

Never put in a prompt what the shared file already says.
