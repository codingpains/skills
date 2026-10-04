# Catalogue conventions (flat-DB row shape + catalogue rules)

Loaded by the **Catalogue Agent** (when drafting specs) and the **Story
Agent** (catalogue mode, when writing rows). It covers the things specific
to cataloguing from code. The **story body format itself is NOT defined
here** — catalogue stories use the same **User Story Format** as
`/quill new-feature` and `/quill change-request`, documented in `~/.claude/skills/quill/agents/story-agent.md`
(`[Persona] — [feature]` title + User Story Statement + Context +
Acceptance Criteria + Out of Scope + Open Questions). Draft to that.

> **Flat DB, not nested pages.** Quill's `storiesDatabase` is a flat Notion
> database. There is no Index page and no per-epic page. An epic is a
> `select` value on the `Epic` property; grouping (Group A/B/C…) is a
> drafting aid for the review gate, not a Notion structure.

## Database row shape

| Field | Value |
|---|---|
| `Story` (title) | The `[Persona] — [feature]` title from the spec. |
| Page body | User Story Statement, Context, Acceptance Criteria, Out of Scope, Open Questions — per the User Story Format in `story-agent.md`. |
| `Story ID` (text) | `<PREFIX>-USR-<NNN>`, zero-padded, sequential. Allocated from **max existing ID in the DB + 1**. Never reuse or renumber. |
| `Epic` (select) | The target epic. If the option doesn't exist yet, it's added to the select first (the command gates this). |
| `Status` (select) | **`Done`** — catalogue stories describe already-shipped behavior. |
| `Figma Link` (url) | Empty. `/quill catalogue-from-code` never generates designs. |
| `Linear` (url) | Empty unless the spec cross-references a ticket. |

## ID allocation

`Story ID` is the source of truth for numbering — there is no external
counter. Before a batch, query `MAX(Story ID)` (parse the numeric suffix;
it's stored as text) and allocate sequentially. On a resume after a
timeout, **re-query the max** rather than trusting an in-memory number.

## Grouping (a drafting aid, not Notion structure)

When a batch has more than ~5 stories, the Catalogue Agent organizes the
**proposed list** under named groups so the user can review it ("Group A —
Page chrome", "Group B — Detail drawer", …). These are for the review gate
only; they do not become Notion pages and do not appear in story bodies.

## Gaps — report-only

`/quill catalogue-from-code` **does not write gap rows.** When the survey turns
up a TODO, a missing permission gate, a likely bug, a `queryKey`
collision, or an undocumented backend contract, the agent collects it in a
**Discovered gaps** section of the run report for the user to act on
manually. It is never created as a row and never marked `Done`.

The gap markers `(gap)` / `_(discovered gap)_` and gap-language ("missing
gate", "no-op", "dead code", "undocumented contract") also act as a
**guard**: if a drafted story turns out to describe a gap rather than
shipped behavior, route it to the gaps report, not to a `Done` row.

(Historical note: the 171 existing rows include a `ONB-USR-072..123`
family of `_(discovered gap)_` rows written under the cataloguer's older
workflow. We do not backfill or recycle these; new gaps are report-only.)

## Cross-references

When one story mentions another, write the ID `XXX-USR-NNN` as plain text
(in Context, an acceptance criterion, or Out of Scope) — not as a Notion
link. Plain-text IDs survive search-and-replace and let the next agent grep
every reference.

## Anti-patterns

- **Bundling unrelated capabilities.** If a story has two unrelated
  acceptance criteria covering different capabilities, split it.
- **Inventing detail.** Every criterion must trace to code actually read —
  no invented paths, hooks, flags, or endpoints. Unsure → Open Questions.
- **Re-deriving an ID.** Never reuse or renumber an existing `Story ID`.
- **Format drift.** Don't invent a body format here — follow the User
  Story Format in `story-agent.md` so catalogue rows match `/quill new-feature`
  output exactly.
