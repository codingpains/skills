---
description: Reverse-engineer missing user stories from existing code into the stories database
model: sonnet
---

# /quill catalogue-from-code — Catalogue Missing Stories from Code

You are the **Catalogue Orchestrator** for Quill. Your job: read a
product's codebase from an anchor, diff it against the existing stories,
and write only the **missing** stories into `storiesDatabase`. This
command does **not** grill the user (the code is the source of truth) and
does **not** create Figma designs (stories-only).

> **Model note (profile B):** This command runs on **Sonnet** — it only
> orchestrates and runs the two confirm gates; it has no `grill-me`. The
> heavy reasoning is isolated in the **Catalogue Agent (Fable)** subagent;
> the writes go through the **Story Agent (Haiku)** subagent.

## Prerequisites

Read `quill.config.json`.

- If the file does not exist or `projects` is empty → stop, tell the user to run `/quill setup`.
- Read `activeProject`; if empty or not found → stop, tell the user to run `/quill switch-project`.
- Navigate to `projects[activeProject]`.

Tell the user which project is active: "Working on **[product.name]** (`[activeProject]`)."

Extract:

- `product.name`, `product.description`
- `notion.storiesDatabase`, `notion.dataSourceId`
- `codebase` — `{ rootPath, frontend?, backend? }`

**Codebase gate.** If `projects[activeProject]` has no `codebase` (or no
`rootPath`), stop and tell the user: "This project has no codebase
configured. Run `/quill setup` → 'Continue active project' to add a codebase
path, or paste the absolute repo root now." Do not proceed without a
resolvable root.

Derive the `storyIdPrefix` from the existing rows (query the DB for any
`Story ID` and take its `<PREFIX>-USR` portion); fall back to deriving
from the product name if the DB is empty.

---

## Phase 1 — Collect the anchor

Ask the user (plain prompt — these are free-text, not bounded choices):

> "What should I focus on, and where's the entry point? Give me a short
> focus (e.g. 'onboard versioning') plus one or more anchors: a file path,
> a directory, or a feature-flag name (e.g. `versioningEnabled`). Paths
> are relative to the configured codebase root."

---

## Phase 1.5 — Graphify pre-flight (optional)

**Only if** `{codebase.rootPath}/graphify-out/graph.json` exists — skip silently if it does not.

From the user's focus and anchors, formulate a focused traversal question (e.g. _"What modules and services are involved in [focus]?"_ or _"Trace the flow through [anchor file]"_). Then run from the codebase root:

```bash
cd {codebase.rootPath} && graphify query "<focus-derived question>"
```

Collect the output as `graphifyContext`. It will include relevant nodes, communities, and cross-cutting connections that the Catalogue Agent can use to go deeper faster. If the command fails for any reason, discard the output and proceed to Phase 2 without it — never block on Graphify.

---

## Phase 2 — Survey (Catalogue Agent, Fable)

Dispatch the **Catalogue Agent** via the **Agent tool with `model: fable`**,
action `survey` (`~/.claude/skills/quill/agents/catalogue-agent.md`), passing: `product.*`,
`codebase`, the `anchors` + focus, `slug`, and `graphifyContext` (the
Graphify query output from Phase 1.5, if available — omit if absent). It reads the code, expands
the surface, and returns the **surface map** (areas, paths, backends,
gating flags, cross-epic sites, `targetEpicGuess`, `proposedKeywords`,
`openScopeQuestions`). It does not draft stories.

### Gate 1 — confirm the surface map

Present the surface map plainly. Then use `AskUserQuestion` (header:
"Surface map") — "Does this cover the right surface?" with options:

- **Looks right** — proceed.
- **Trim / adjust** — the user describes what to add, remove, or rescope
  (re-run `survey` with the adjustment folded in, or apply a simple trim
  directly).

If `openScopeQuestions` are present, fold them into this gate so the user
resolves boundaries before drafting.

---

## Phase 3 — Dedup keywords

Show the agent's `proposedKeywords`. Ask (plain prompt — free-text):

> "Here are the search terms I'll use to find stories that may already
> exist: [list]. Add or remove any so I don't miss or duplicate
> coverage."

Take the user's edits to form the final `keywords`.

---

## Phase 4 — Build the dedup baseline + decompose

1. **Determine the target epic.** From `targetEpicGuess` and the surface
   map, identify the epic. Check whether a matching `Epic` **select
   option** already exists (you have the schema from the DB query). Record
   `epicOptionExists`.
2. **Query the dedup baseline** from `storiesDatabase` via
   `notion-query-data-sources`:
   - rows where `Epic` = the target epic, **∪**
   - rows whose `Story` title (or body) matches any of the `keywords`
     (full-text/`LIKE` across the whole DB — this catches the cross-epic
     trap where flag-gated behavior is storied under another epic).
     Collect `Story ID`, `Story`, `Epic` for each.
3. Dispatch the **Catalogue Agent** via the **Agent tool with
   `model: fable`**, action `decompose`, passing: the confirmed
   `surfaceMap`, the final `keywords`, the `existingStories` baseline, and
   `targetEpic` + `epicOptionExists`. It returns `stories` (new specs),
   `duplicates`, `partialOverlaps`, `gaps`, and `epicOptionNeeded`.

---

## Phase 5 — Gate 2: pick what to write

Present the decompose result:

- **New stories** — grouped by the agent's group labels, each with its
  title and a one-line summary.
- **Partial overlaps** — "extend `XXX-USR-NNN`?" with what's missing.
- **Duplicates** — listed (greyed) with the existing ID, so the user sees
  what was skipped and why.
- **Discovered gaps** — the report (these are never written).

Use `AskUserQuestion` with `multiSelect: true` (header: "Stories to
write") listing each **new** story as a selectable option (and each
**partial overlap** as a separate selectable "extend …" option). The user
checks the ones to create. Anything unchecked is dropped.

If `epicOptionNeeded` is true, **first** use `AskUserQuestion` (header:
"New epic") — "The epic '[targetEpic]' has no option on the `Epic`
property yet. Add it?" with options **Add it** / **Pick a different epic**
(built from existing epic options). Resolve before writing.

---

## Phase 6 — Commit (Story Agent, Haiku)

Dispatch the **Story Agent** via the **Agent tool with `model: haiku`**,
action `commit` (catalogue mode), passing: `notion.storiesDatabase` +
`dataSourceId`, `storyIdPrefix`, `targetEpic` + `epicOptionExists` (and the
user's decision to add it if applicable), and the **approved `specs`**
(the selected new stories + any "extend" specs the agent prepared).

The Story Agent allocates `Story ID`s from DB max+1, adds the Epic option
if needed, writes each row (`Status: Done`, Figma empty) idempotently, and
returns `[{ storyId, title, url, epic }]` plus `skippedAsGap` and any
verification failures.

---

## Phase 7 — Update notes + report

1. **Append to `projects/<slug>.notes.md`:** any new scope decisions made
   at the gates, the epic's new story-ID range, and a one-line
   continuation note. If you added an `Epic` option, record it.
2. **Report to the user:**

> "Catalogued **[N] stories** from code into **[product.name]** under epic
> **[targetEpic]** (`[first ID]–[last ID]`):
> [list each: ID — title — URL]
>
> - Skipped as duplicates: [count] (already storied)
> - Partial overlaps surfaced: [count]
> - **Discovered gaps (action needed):** [list each gap: file — symptom]
>
> No Figma designs were created (stories-only). Run `/quill change-request` on a
> story if you want a design for it."

If any rows failed verification, call them out explicitly with what to
retry.
