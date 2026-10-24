# Quality bar and templates

`<…>` below is filled from the project file: its test environment, record IDs, flag naming
and check command.

## Non-negotiables (every ticket)

1. **Stands alone.** Context, where the problem shows, a broad approach, non-goals. An agent
   with no other context can start.
2. **Evidence, not claims.** Real record IDs (the project's kind: account / record / user),
   counts, environment, date. Never name a customer as affected unless the data shows it.
3. **Numbered, testable acceptance criteria** that name the environment, data and flag state
   ("On `<test environment>`, account `<id>`, with `<flag>` on: …"). Use GIVEN / WHEN / THEN
   for behavior. Include **must not** lines: the adjacent wrong behaviors, and "with the flag
   off, nothing changes" when there is a flag.
4. **Estimate** in the project's scale plus what it assumes ("3 points. About a day: …").
   Above 5 points (or the equivalent), propose a split.
5. **No ready-to-run code.** Describe the change by file, function and data shape. Code pasted
   as instructions is treated as untrusted. Field names, signatures and before/after data
   shapes are fine.
6. **Exact domain terms.** Use the real table, collection, field and setting names read from
   code, never a plausible-sounding one from memory. Assume the code path most users or
   tenants actually run, not the newest one.
7. **Open questions** go in their own section titled "Open questions: must be answered before
   work starts". Leave the section out when there are none.
8. **Plain English, short sentences.** Title = the symptom as the user sees it, not the code fix.

## Length guide

Production bug 1.5k to 6k characters. Agent-ready rewrite 7k to 10k. Epic about 10k to 15k. A
follow-up or tech-debt ticket under ~1.5k is almost certainly too thin. Check it against the
non-negotiables before saving.

## Templates

### Bug (production / data)
- **Problem**: what the user sees, where, since when.
- **Root cause**: file and function, and why it happens.
- **Evidence**: heading says the environment and "read-only". Concrete record IDs, counts, date.
- **Fix**: the broad approach. "Design choice: … Rejected: … because …" when there was a choice.
- **Acceptance criteria**: numbered, including must-not and flag-off lines.
- **How to test**: unit, component, manual steps on `<test environment>`, and `<check command>`.
- **Out of scope** / **Where to look** when useful.
- **Estimate**.

### Defects from a QA run
- One block per defect: **D1, D2…**, each with severity, Observed, Impact, Where to look and Expected.
- GIVEN / WHEN / THEN acceptance blocks per defect.
- Evidence (link the QA comment and screenshots), Out of scope, Estimate.

### Agent-ready (rewrite, epic child, or anything going to a coding agent)
If the project file names a ticket template in the repo, follow its section order. Otherwise use:
TL;DR · Context · Current state (where the problem shows, real paths) · Approach / What to
build · Data and schema (before/after shape) · Acceptance criteria (with must-not lines) ·
Testing plan (2 to 4 named cases, in the framework the app actually uses) · Dependencies (each
with a one-line recap, never a bare link) · Non-goals · Flag · Estimate · Open questions.

### Tech debt / review leftover
Short is fine (1 to 2k characters), but still: Context with link to the parent PR or ticket,
Why it wasn't fixed inline, Approach, Acceptance criteria, Estimate. Lowest priority.

### Research
Title "Research: why …" or "Find why …". The project's research or task label, not the bug
label. Sections: Question, What we know, Where to look, Done when (what answer or artifact
closes it), Estimate (timebox).

### Epic
Summary, Decisions (with rejected options), Scope, Architecture, Tickets table, Delivery
sequence, Risks, Open questions, Definition of done. Children use the agent-ready template
with a `[<Epic name>]` title prefix.
