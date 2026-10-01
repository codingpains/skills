# Handoff packet

The Lead sends this as the agent's prompt. Subagents see nothing else from
the main session, so leave nothing implicit. Fill every field; write `none`
rather than dropping a field.

```
# <Stage> — <TICKET_ID>: <title>

Read first: ~/.claude/skills/team-lead/references/team-rules.md
Report format: ~/.claude/skills/team-lead/references/stage-report.md

## Where
Worktree: <absolute path>   # all your work happens here; see team-rules § Scope
Branch: <branch> (checked out in the worktree)
Base commit: <sha>   # diff everything against this: git diff <sha>...HEAD (in a review round, the round's base)
Default branch: <name>
Repo profiles: <absolute paths, each with its `paths` scope, or "none: work the checks out yourself">
Run directory: ~/.team-lead/runs/<TICKET_ID>/  # the Lead's state; write here only when your agent file says so

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
<Planbin plan ID and URL, or "no plan: trivial ticket, the brief is the spec",
or "no plan: review round <n>, the items in Round are the spec">

## Round
<"none", or for a review round (SKILL.md § Review rounds):
Round: <n>   PR: <url>   PR base: <run.json base>   # Base commit above is the round's base
Items (the round's acceptance criteria; the ticket's ACs must still hold):
| # | Source | Asks for | Files | Size |
...the rows of round-<n>/items.md this stage acts on>

## Previous stages
<for each earlier stage: its status, commits, validations, and concerns,
copied from its report; the full report for the immediately previous stage>

## Your task
<the stage's task in one or two sentences; for Wrap-up, the numbered fix
list from review-fixes.md verbatim>
```

Keep the packet under about 400 lines. When earlier reports are long, keep
the immediately previous one whole and cut the older ones to status, commits,
validations and concerns.
