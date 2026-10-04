# Quill — Software Design Assistant

Quill is an agentic architecture that helps design software by producing user stories and aligned Figma designs. It uses a Socratic interrogation process to extract requirements, stores stories in Notion, and generates designs in Figma.

## First-time setup

Run `/quill setup` before anything else. It will ask you about:

- The product you are working on
- Which Notion workspace / database to use (or create one)
- Which Figma file to use (or create one)

Config is persisted to `quill.config.json` in Quill home (`$QUILL_HOME`, else `~/.quill/`), outside the skills repo. Quill supports **multiple projects** — each has its own Notion database and Figma file. One project is active at a time.

## Main commands

| Command                | What it does                                                                                                                                             |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/quill setup`               | Add a new project or resume — discovers Notion DB and Figma file                                                                                         |
| `/quill switch-project`      | Switch the active project or add a new one                                                                                                               |
| `/quill new-feature`         | Grills you on a new feature → writes user story to Notion → generates Figma design                                                                       |
| `/quill change-request`      | Finds related stories → grills you on the change → updates stories and designs                                                                           |
| `/quill groom`               | Grooms a ticket from Linear or a Notion tasks database (audit → grill → **additive** update) → syncs the matching Notion user story (no Figma)           |
| `/quill catalogue-from-code` | Reads the codebase from an anchor → diffs against existing stories → writes only the **missing** stories to Notion (stories-only, no grilling, no Figma) |
| `/quill polish-ui`           | Refactor the design layer — extract components/tokens, retheme, audit inconsistencies → syncs to Notion design system spec                               |

## Workflow overview

```
/quill setup ──────────────────────────────────────────────► quill.config.json
                                                        activeProject + projects{}
/quill switch-project ─────────────────────────────────────► updates activeProject

(all commands below operate on the active project)

/quill new-feature
    │
    ├─ 1. Socratic grilling (grill-me skill)
    ├─ 2. Story Agent → Notion user story page
    └─ 3. Design Agent → Figma screen linked to story

/quill change-request
    │
    ├─ 1. Search Notion for related stories
    ├─ 2. Present findings to user
    ├─ 3. Socratic grilling on the change
    ├─ 4. Story Agent → update Notion stories
    └─ 5. Design Agent → update Figma designs

/quill groom  (ticket grooming from Linear or Notion tasks — no Figma)
    │
    ├─ 1. Resolve active project + ticket source (Linear and/or notionTasks config)
    ├─ 2. Fetch the ticket (Linear issue or Notion task row) → audit for gaps (4 categories)
    ├─ 3. Grill in batches, one category at a time
    ├─ 4. Draft the groomed update (preview)  [Gate]
    │         Linear: additive description. Notion task: additive page body +
    │         Acceptance Criteria property refined in place + Status Backlog→Ready
    ├─ 5. Write back: save_issue (Linear) or notion-update-page (Notion task)
    ├─ 6. Story Agent (Haiku, create/update) → sync Notion story  [Gate]
    │         → set the row's back-link property (Linear, or Task Link for Notion tasks)
    └─ 7. Wrap up / loop to the next ticket

/quill catalogue-from-code  (no grilling, no Figma — reverse-engineers stories from code)
    │
    ├─ 1. Resolve active project + codebase root (requires projects[*].codebase)
    ├─ 2. Catalogue Agent (Fable) → survey code → surface map  [Gate 1]
    ├─ 3. Derive + augment dedup keywords (free-text)
    ├─ 4. Dedup baseline: query DB by epic ∪ keyword search
    ├─ 5. Catalogue Agent → decompose → classified specs + gaps report
    ├─ 6. Pick stories to write (multi-select)  [Gate 2]
    └─ 7. Story Agent (Haiku, catalogue mode) → write missing rows (Status: Done)
              → append scope decisions to projects/<slug>.notes.md

/quill polish-ui  (no user stories — design layer only)
    │
    ├─ 1. Scan Figma file (pages, components, variables)
    ├─ 2. Choose mode: Componentize / Tokenize / Retheme / Audit
    ├─ 3. Select scope (all pages / specific pages / specific frames)
    ├─ 4. Mode-specific interrogation
    ├─ 5. Preview change plan (user confirms before any writes)
    ├─ 6. Polish Agent → execute in Figma
    ├─ 7. Check story link drift (update Figma links in affected Notion stories)
    └─ 8. Update Notion design system spec (components, tokens, changelog)
```

## Config file (`quill.config.json`)

Created and maintained by `/quill setup` and `/quill switch-project`. Never edit it manually unless you know what you're doing. Top-level shape: `activeProject` (a slug) plus `projects` (slug → product/notion/codebase/linear/figma/metadata). See the "Config schema reference" section in `~/.claude/skills/quill/commands/setup.md` for the full field-by-field shape, including the Figma page-role convention.

## Agent prompts

Specialized prompt files live in `agents/`. They are loaded by the commands as needed:

- `~/.claude/skills/quill/agents/story-agent.md` — structures requirements into Notion user stories (create/update modes from a grill transcript; **catalogue mode** writes code-derived rows for `/quill catalogue-from-code`)
- `~/.claude/skills/quill/agents/catalogue-agent.md` — reads code, expands a feature surface, dedups against existing stories, and drafts the missing stories as specs (Fable; used by `/quill catalogue-from-code`)
- `~/.claude/skills/quill/agents/design-agent.md` — translates stories into Figma screens
- `~/.claude/skills/quill/agents/polish-agent.md` — executes structural Figma refactoring (components, tokens, retheme, audit fixes)

Shared references loaded by these agents live in `references/`:

- `~/.claude/skills/quill/references/story-conventions.md` — the flat-DB row shape + story-body format (catalogue mode)
- `~/.claude/skills/quill/references/notion-quirks.md` — idempotent batch-write rules (catalogue mode)

Per-project catalogue state (code-surface map + settled scope decisions) lives in `projects/<slug>.notes.md`, read and appended by `/quill catalogue-from-code`.

## Model policy (profile B)

Each task runs on the cheapest model that meets its demand. Two levers set the model:

1. **Command frontmatter `model`** — the main-loop model the command was tuned for. Quill now runs as one skill, so this is advisory: the session model runs the command. This covers everything that _must_ run in the loop: `grill-me` (interactive), all `AskUserQuestion` confirm gates, and orchestration glue. Background subagents can't run interactive dialogue, so anything interactive inherits the command's model.
2. **Agent tool `model` override** — each specialized agent is dispatched as a **non-interactive subagent** with a fixed model. The orchestrating command owns the user gates and runs each agent in two passes: a `draft`/`plan` pass (compute, return, no writes) and a `commit`/`generate` pass (execute after approval).

| Task                                          | Where it runs                                    | Model      | Why                                                                                                                                                                                                                                      |
| --------------------------------------------- | ------------------------------------------------ | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `grill-me` interrogation                      | main loop (in `/quill new-feature`, `/quill change-request`) | **Fable**  | Quality compounds — drives everything downstream                                                                                                                                                                                         |
| Story Agent (create/update + catalogue write) | subagent                                         | **Haiku**  | Low-reasoning structuring/writing of an already-curated draft or spec                                                                                                                                                                    |
| Catalogue Agent                               | subagent                                         | **Fable**  | Highest-reasoning read side — code comprehension + decomposition quality compounds across the whole batch (same rationale as `grill-me`)                                                                                                 |
| Design Agent                                  | subagent                                         | **Sonnet** | Spatial/layout reasoning + many `use_figma` calls                                                                                                                                                                                        |
| Polish Agent                                  | subagent                                         | **Fable**  | Highest-risk, highest-reasoning (destructive Figma edits)                                                                                                                                                                                |
| `/quill setup`, `/quill switch-project`                   | main loop                                        | **Haiku**  | Config CRUD + discovery                                                                                                                                                                                                                  |
| `/quill new-feature`, `/quill change-request`             | main loop                                        | **Fable**  | Hosts `grill-me`; story/design work is delegated to subagents at their own tiers                                                                                                                                                         |
| `/quill groom`                                      | main loop                                        | **Fable**  | Hosts the interactive gap audit + batched interrogation (same can't-delegate-interactive rationale as `/quill new-feature`). The Notion story write is delegated to the Haiku Story Agent; the ticket-source write-back (Linear `save_issue` or Notion `notion-update-page`) is a single gated MCP call inline |
| `/quill catalogue-from-code`                        | main loop                                        | **Sonnet** | Orchestration + two confirm gates only; no `grill-me`. The heavy read-reasoning is the Fable Catalogue Agent subagent; writes go to the Haiku Story Agent                                                                                |
| `/quill polish-ui`                                  | main loop                                        | **Sonnet** | Bounded mode-specific interrogation + planning; the destructive work is the Fable Polish Agent subagent                                                                                                                                  |

**Constraint that shaped this:** `grill-me` and the confirm gates are interactive, so they can't be isolated to their own model — they inherit the command's frontmatter model. That's why `/quill new-feature` and `/quill change-request` are Fable (to give `grill-me` Fable) even though their orchestration glue is light. The genuinely expensive autonomous work is still delegated out at the right tier.

When adding a new agent or command, set its model the same way: pin autonomous agents via the Agent tool `model` override; set interactive work via command frontmatter to match its most demanding in-loop task.

## Asking the user for feedback

Quill is interactive — it constantly stops to let the user choose a mode, confirm a plan, or pick which items to act on. **Whenever Quill needs the user to choose between a bounded set of options, use the `AskUserQuestion` tool instead of writing the options as prose and waiting for a typed reply.**

Guidelines:

- **Use `AskUserQuestion` for bounded choices** — setup mode, polish type, scope, "which of these stories/patterns?", confirm/adjust/cancel gates, yes/skip toggles, picking the active project, choosing a Figma page. Map each lettered option to one `AskUserQuestion` option with a short `label` and a `description` explaining the trade-off. Use `multiSelect: true` when the user may pick several (e.g. selecting affected stories, standard pages, componentization patterns). Build options dynamically from config or scan results where the choices are data-driven (project list, related stories, audit categories).
- **For confirm-or-correct gates** (story drafts, design plans, change plans, discovery reports), offer options like "Looks good" and "Make changes" — the user picks "Make changes" (or the auto-provided "Other") to type corrections in their own words.
- **Do NOT use `AskUserQuestion` for free-text input** — product name, descriptions, pasting Notion/Figma URLs, naming a component, defining variants, or pasting a color palette. Ask those as plain prompts; there is no bounded option set.
- **Do NOT use `AskUserQuestion` during `grill-me` Socratic interrogation** — that process is intentionally open-ended dialogue, one question at a time. Let the skill drive it conversationally.
- After the user answers, proceed using their selection. Respect a denied/closed question by re-asking differently rather than repeating the same call.

## Rules for all agents

1. Always read `quill.config.json` and navigate to `projects[activeProject]` before any Notion or Figma operation.
2. Always tell the user which project is active at the start of `/quill new-feature`, `/quill change-request`, and `/quill groom`.
3. Every Notion story page must include: title, user story statement, acceptance criteria, and a link to the Figma screen. `/quill catalogue-from-code` uses the **same User Story Format** as `/quill new-feature` and `/quill change-request` (`[Persona] — [feature]` title + statement + Context + Acceptance Criteria + Out of Scope + Open Questions). **Exception:** because it reverse-engineers already-shipped code, it is stories-only — it leaves `Figma Link` empty and sets `Status: Done`.
4. Every Figma screen must include the Notion story URL in its description.
5. Never create a design before there is a linked story. (`/quill catalogue-from-code` creates no designs at all — see rule 3's exception.)
6. When updating a story, always check if the linked design needs updating too.
7. Never mix data between projects — each project's Notion DB and Figma file are isolated.
8. `/quill polish-ui` never creates user stories. It writes only to Figma and the Notion design system spec (a separate page from the stories database).
9. After any `/quill polish-ui` session that renames or moves frames, always check for story link drift and update affected Notion stories.
10. For every bounded-choice decision, present options via `AskUserQuestion` (see "Asking the user for feedback" above). Reserve plain prompts for free-text input and `grill-me` interrogation.
11. `/quill catalogue-from-code` requires `projects[activeProject].codebase.rootPath`. It reads code but never modifies it. All anchors resolve relative to the configured codebase roots. It writes only to `storiesDatabase`, which is the single source of truth for stories and for `Story ID` allocation (max existing ID + 1 — there is no external counter).
12. `/quill catalogue-from-code` never writes gap rows. Discovered gaps (TODOs, missing gates, likely bugs, undocumented contracts) are **report-only** — surfaced in the run report for the user to act on, never marked `Done`. The `user-stories-cataloguer` skill that previously did code→stories work is **retired**; Quill is the sole system. Its methodology now lives in `references/` and `projects/<slug>.notes.md`.
13. `/quill groom` is project-scoped: it reads the active project's `notion.storiesDatabase` and the optional `projects[activeProject].linear` and/or `projects[activeProject].notionTasks` blocks — a project may have either, both, or neither ticket source configured, and `notionTasks` may point at a database shared across multiple projects (e.g. a shared backend tasks DB). It writes no Figma. Its ticket-source edits are **additive-first**: for Linear, groomed content is prepended to the description, then a `--` separator, then `## Original Description` with the original copied verbatim — never deleted, summarized, or reordered. For a Notion task, the same additive pattern applies to the page body, but the `Acceptance Criteria` property is refined **in place** (it's a current-state field, not a history) and `Status` moves **forward only** (`Backlog` → `Ready`, never backward, never touched once past `Backlog`) as the groomed signal in place of Linear's `Groomed` label. Not every groomed ticket gets a story — backend/infrastructure tickets with no persona-facing behavior may be ticket-only; `/quill groom` asks rather than assuming. When a story is written, it syncs via the **same User Story Format** as `/quill new-feature` (reusing the Haiku Story Agent in create/update mode) and sets the row's back-link property to the ticket URL — **`Linear`** for a Linear-sourced ticket, **`Task Link`** for a Notion-tasks-sourced ticket. Never write a Notion task's URL into a property named `Linear` on a project that has no Linear ticket source at all — the property name must match the project's actual ticket source, not Quill's Linear-first history. If the resolved property doesn't exist on the stories database yet, `/quill groom` gates adding it with the user before writing. The standalone `groom-ticket` skill that previously did this is **retired**; `/quill groom` is the sole entry point.
14. **Graphify is optional but should be used when present.** Before any code exploration in `/quill catalogue-from-code` (Phase 1.5) and `/quill groom` (Phase 1.5), check whether `{codebase.rootPath}/graphify-out/graph.json` exists. If it does, run `graphify query "<focused question>"` from `codebase.rootPath` and pass the output as context to the downstream agent or gap audit. Never block on it — if the file is absent, the binary is missing, or the query fails for any reason, skip silently and proceed. The query output lives only in the current run; never persist it.
