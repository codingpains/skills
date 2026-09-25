---
name: groom
description: "Clarify an unclear ticket by answering its open questions from the code, docs, git history and related tickets, scoring each answer 1–3 for confidence and escalating anything below 2 to a human with suggested options. Run by /team-lead during intake; also usable alone as /groom TICKET_ID [questions]."
argument-hint: "TICKET_ID [question; question; ...]"
---

# groom

Turn an unclear ticket into answered questions, each with a confidence score
and the evidence behind it. Read
`~/.claude/skills/team-lead/references/confidence-scoring.md` first: it owns
the scale, the escalation rule and the output formats.

Arguments: `$ARGUMENTS`. The first word is the ticket ID; anything after it is
a `;`-separated list of questions. When `/team-lead` runs this skill it passes
the questions it found. When there are none, derive them yourself (step 1).

## 1. Questions

Fetch the ticket if it is not already in context (Linear:
`mcp__claude_ai_Linear__get_issue` and `list_comments`, loaded with
`ToolSearch`; GitHub: `gh issue view <id> --comments`).

Without a question list, write one. A question is worth asking when its
answer changes what gets built or how it is tested: missing acceptance
criteria, an undefined term, a named screen/field/endpoint you cannot locate,
conflicting statements, undefined behavior for empty input, errors,
permissions or existing data. Skip questions whose answer would not change
the code.

## 2. Research

For each question, search in this order and stop when you have a score-3
answer:

1. **The ticket's own world**: comments, parent and sub-issues, linked
   issues and documents, and Linear issues that mention the same feature
   (`mcp__claude_ai_Linear__list_issues` with a query).
2. **Code**: `Grep`/`Glob` for the names the ticket uses, then the
   neighbours of what you find: callers, the tests (tests state behavior
   most reliably), sibling features that solve the same problem.
3. **Docs**: `README*`, `docs/`, ADRs, `CLAUDE.md`, `AGENTS.md`,
   `.claude/rules/`, API schemas, OpenAPI/GraphQL definitions.
4. **History**: `git log -S '<term>' --oneline`, `git log --grep '<term>'`,
   and `git blame` on the lines that matter; the PR or ticket a commit
   references often holds the reasoning.

With more than about five questions, or questions spread across unrelated
parts of the codebase, spawn `Explore` agents in parallel, one per cluster
of questions, and ask each for file:line evidence, not conclusions alone.

Record for every answer: what you searched, what you found, and the exact
citation. A citation is a path with a line number, a doc heading, a ticket
comment link, or a commit SHA.

## 3. Score

Score each answer with the scale. Be strict: a 3 needs a citation that
states or shows the answer; a 2 needs written-down examples that imply it and
nothing that contradicts it; everything else is a 1.

## 4. Output

Print:

1. The answer table from `confidence-scoring.md`, one row per question.
2. One escalation block per score-1 question, with two to four options,
   recommended option first.
3. One line: `N answered (x at 3, y at 2), M escalated`.

Then:

- **Run by `/team-lead`**: stop here. The Lead writes the answers into the
  brief and asks the human about the escalations.
- **Run alone**: ask the human about the escalations with `AskUserQuestion`
  (up to four per call, the options from the escalation blocks, recommended
  first), and finish with the full table updated with their answers, marked
  `human decision`. Offer to post the table as a comment on the ticket; post
  only if they say yes.
