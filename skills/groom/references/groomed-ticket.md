# The groomed ticket

What `/groom` writes, how it checks it, and how it goes back to the tracker.

## Type and template

Pick the ticket's type from `/ticket`'s `standards.md` § Templates and use
that template: **Bug** (production or data), **Defects from a QA run**,
**Agent-ready** (anything a coding agent or an engineer builds: the
default for a feature, an epic child, a rewrite), **Tech debt / review
leftover**, **Research**, **Epic**. When the profile's *Tracker* names a
repo template (`ticket-tree`), its section order wins for agent-ready
tickets, as `standards.md` says. Match the length guide for the type.

## Writing it

`groomed.md` holds, in order:

```
Title: <kept, unless it is misleading; a symptom as the user sees it, never the code fix>
Estimate: <points, with what it assumes, from Decisions>
Labels: <existing + Groomed + defaults.md's for the team, with any you added marked>
Priority: <existing, or the one you picked and why, only when it was empty>
Story: <yes: persona-facing behavior in the ACs | no: <reason>>

---
<the template's sections, filled>

--

## Original Description
<the original, verbatim, or "(no original description)">
```

Everything above the first `---` is for the writer and the final message;
everything below is the description. The original stays verbatim after
the `--` separator, as `/quill groom` keeps it: never deleted, shortened
or reordered. A Notion task keeps the same shape in its page body; its
`Acceptance Criteria` property takes the criteria alone.

Filling the sections, from `decisions.md`:

- A decision is **settled fact**. No "proposed", "to confirm", "likely".
  A technical 1 reads `Design choice: … Rejected: … because …`.
- Every path, function, collection, field, flag and type name comes from a
  research row with a score of 3. A name nobody verified is described in
  words, not named.
- **Evidence** carries the records Q-real found, under a heading that says
  the environment and `read-only`. A customer appears only when the data
  showed it. When Q-real found nothing, the ticket says the problem is
  unconfirmed and what would confirm it.
- **Acceptance criteria** are numbered, name the environment, the company
  or data and the flag state, use GIVEN / WHEN / THEN for behavior, and
  end with the must-not lines: the adjacent wrong behaviors, and
  `with the flag off, nothing changes` when there is a flag.
- **Testing plan**: two to four named cases, in the framework the profile
  says that area uses.
- **Dependencies**: each with a one-line recap, never a bare link. The
  related ticket Q-dup found goes here; a likely duplicate is named as
  one, with the recommendation, and left for `/ticket rearrange`.
- **Open questions: must be answered before work starts** exists only when
  `research.md` § Ask left something unanswered. With nothing left, no
  section.
- No runnable code. Field names, signatures and before/after data shapes
  are fine.
- Words Linear auto-links (`I-9`) are rephrased or escaped.

## Self-check

Before the writer runs, check `groomed.md` against this list and fix what
fails. Each line is one of `standards.md`'s non-negotiables or a
`pitfalls.md` entry, stated as a test:

1. Every cited name has a score-3 row in `research.md`.
2. Every claim about scale or a customer has a record in *Evidence*.
3. Every acceptance criterion names environment, data and flag state, and
   the list ends with must-not lines.
4. The estimate states its assumptions; above 5 it was asked (§ Ask).
5. No code block that could be pasted and run.
6. No "proposed" or "to confirm" wording where a decision exists.
7. Length is inside the type's guide; a follow-up under 1.5k characters is
   thin until it is not.
8. The original description is present and verbatim.
9. The title is the symptom, not the fix.

Then the **cold reader**: one `general-purpose` agent on `haiku`,
description `Cold read — <KEY>`, given only the description part of
`groomed.md` and the profile's *Glossary*, with this prompt:

```
You are an engineer who has never seen this ticket's project. You have
only the text below. List, as numbered lines, each thing that would stop
you from starting work on it today: a term you cannot resolve, a file or
screen you could not find from the text, an acceptance criterion you could
not test as written, a step with two readings. Return "none" when you
could start. Return the list and nothing else.
```

Write its answer to `cold-read.md`. Fix each item from the research you
hold, or with one more targeted researcher when a name is missing. Run it
once more. What still fails goes under Open questions, and the groom goes
on.

## Writer

One `general-purpose` agent on sonnet, description `Write back — <KEY>`.
It gets the paths of `groomed.md`, `ticket-source.md` and the profile, the
flags, and this brief. A ticket that already met the bar (SKILL.md § 2)
sends `label only`: the writer then does steps 2 and 3 alone. It loads Linear's or Notion's tools with
`ToolSearch` (Notion's server is the intake reader's *Notion server*
line), and returns one line per change, nothing else.

```
1. Ticket. Linear: save_issue with the title and the description part of
   groomed.md; the estimate only when the field is empty; the priority only
   when it was empty. Notion task: notion-update-page with the page body,
   the Acceptance Criteria property set to the criteria alone, and Status
   Backlog → Ready, only from Backlog (quill groom Phase 5).
2. Labels (Linear). list_issue_labels; the Groomed label exists or is
   created (#7C3AED); save_issue with the merged set from groomed.md's
   Labels line, each label once. Adding Bug attaches an SLA: say so in the
   result.
3. Check (/ticket Step 4). get_issue or notion-fetch again: headers not
   duplicated, markdown clean, no unwanted auto-link, labels not doubled,
   estimate, parent and relations as intended. Fix and re-check once.
4. Story, unless --no-story or groomed.md says Story: no (quill groom
   Phase 6 without its gates). Find the row in the project's
   storiesDatabase by the back-link property (Linear, or Task Link for a
   Notion task) first, then by title; a confident match is update mode,
   anything else is create mode. Dispatch
   ~/.claude/skills/quill/agents/story-agent.md with the Agent tool on
   haiku: action draft with the groomed Goal, criteria, out of scope and
   open questions as the transcript, then action commit. Set the back-link
   property to the ticket URL. A missing back-link property: skip the
   link, say so; never change the database schema.
5. Write <run dir>/result.md: ticket URL, labels now on it, estimate,
   priority, status, story URL or why none, each check's outcome, every
   error.
```

The story rule: a ticket has a story when its acceptance criteria describe
behavior a persona sees or does (a screen, a message, a document, a
customer-facing API). Plumbing, migrations, refactors, observability,
tests and tech debt have none. Decide it in `groomed.md`'s `Story:` line
and say why; it is never a question for Gustavo.
