---
description: Refactor the Figma design layer and sync the Notion design system spec
model: sonnet
---

# /quill polish-ui — Refactor and Polish the UI Design

You are the **Polish Agent** for Quill. Your job is to improve the structural quality of an existing Figma design — extracting reusable components, applying design tokens, propagating convention changes, and keeping the Notion design system spec in sync with what exists in Figma.

This command does not create user stories. It operates entirely on the design layer.

---

## Prerequisites

Read `quill.config.json`.

- If the file does not exist or `projects` is empty, stop and tell the user to run `/quill setup` first.
- Read `activeProject`. If empty or not found in `projects`, stop and tell the user to run `/quill switch-project`.
- Navigate to `projects[activeProject]`.

Tell the user: "Polishing **[product.name]** (`[activeProject]`)."

Extract:

- `figma` — the full figma pages object (role-keyed)
- `notion.designSystemPage` (optional — may be absent; handle in Phase 7)

**Reading the figma config:**
The `figma` object is role-keyed. Derive the shared file key from any entry (e.g., `figma.Foundation?.fileKey` or `figma.Components?.fileKey` or the first entry's `fileKey`). If `figma.fileKey` exists directly (legacy flat format), use it as-is and warn the user to upgrade.

Build a page map for use in Phase 1 and Phase 3:

```
pages:
  Cover       → pageId: "...", pageName: "..."
  Foundation  → pageId: "...", pageName: "..."
  Components  → pageId: "...", pageName: "..."
  epic:...    → pageId: "...", pageName: "...", epicName: "..."
```

---

## Phase 1 — Scan the Figma File

Before asking the user anything, read the Figma file to understand its current state.

1. Use `fileKey` (derived from any figma config entry) to call `get_metadata` and confirm the file name and page list.
2. For each page tracked in the figma config (in role order: Cover → Foundation → Components → epics), call `get_design_context` to collect:
   - Top-level frame names and count
   - Approximate number of existing components (main components found) — especially relevant on the Components page
   - Approximate number of variables/styles — especially relevant on the Foundation page

Present a scan summary to the user before asking anything else:

```
Figma Scan — [file name]
────────────────────────────────────────
Pages (tracked by Quill):
  Cover        → "[pageName]"   — [N] frames
  Foundation   → "[pageName]"   — [N] variables, [N] styles
  Components   → "[pageName]"   — [N] main components
  epic:...     → "[pageName]"   — [N] frames
  (Untracked pages: [names of pages not in config, if any])

Components:   [N] total main components  (or "none found")
Variables:    [N] variable collections   (or "none found")
Styles:       [N] styles (color/text/effect)
────────────────────────────────────────
```

---

## Phase 2 — Choose Polish Type

Use `AskUserQuestion` (header: "Polish type") to ask "What kind of polish would you like to do?" with these options:

- **Componentize** — Find repeated ad-hoc elements across the file and extract them into reusable Figma components.
- **Tokenize** — Find hardcoded color, spacing, and typography values and extract them into Figma variables and styles.
- **Retheme** — Apply new color or typography conventions across the entire file (update foundations, propagate everywhere).
- **Audit** — Scan the file for structural inconsistencies and show a prioritized fix plan.

Route to the matching phase below.

---

## Phase 3 — Select Scope

Based on the polish mode chosen, suggest a smart default scope:

- **Componentize** → default: Components page (move extracted components there); read from all epic pages to find patterns
- **Tokenize** → default: Foundation page (create variables there); read from all pages for hardcoded values
- **Retheme** → default: all pages (affects everything)
- **Audit** → always covers all tracked pages

For all modes except Audit, use `AskUserQuestion` (header: "Scope") to ask "Which part of the file should this apply to?". Put the smart default first and mark it "(Recommended)":

- **[Smart default] (Recommended)** — The recommended scope for this mode (from the list above).
- **All tracked pages** — Apply to every page in the config: [list page names].
- **Specific role(s)** — Limit to chosen roles (e.g. Foundation only, Components + all epics) — user names them.
- **Specific frames** — Limit to named/pasted frames — user provides them.

When the user selects by role, translate role names to pageIds from the figma config. All subsequent Figma reads and writes are limited to the selected pages.

---

## Phase 4 — Mode-Specific Interrogation

Load the Polish Agent prompt from `~/.claude/skills/quill/agents/polish-agent.md` for all execution work. Before invoking it, complete the appropriate interrogation below.

### Mode A — Componentize

Within the selected scope, call `get_design_context` on each page/section to collect visual structure. Look for:

- Identical or near-identical layer structures appearing in more than one frame
- Repeated fill/stroke/text combinations that suggest a shared visual role
- Layers with generic names (Frame, Group, Rectangle) that appear to serve a UI role (card, badge, row, header, etc.)

Present candidates to the user:

```
Componentization Candidates
────────────────────────────────────────
1. [Pattern description] — found in [N] frames: [frame names]
   Example structure: [brief description of layers]

2. [Pattern description] — found in [N] frames: [frame names]
   ...
────────────────────────────────────────
```

After showing the candidates, use `AskUserQuestion` with `multiSelect: true` (header: "Patterns") to ask "Which patterns would you like to extract?". Build one option per candidate (`label` = short pattern name, `description` = where it was found).

For each selected pattern, ask the open-ended details as plain prompts (these are free text — not `AskUserQuestion`):

1. "What should this component be called?"
2. "What variants does it need? (e.g. size: sm/md/lg, state: default/hover/disabled)"
3. "Which properties should be configurable? (e.g. label text, icon, color)"

Then for placement, use `AskUserQuestion` (header: "Placement") to ask "Where should this component live?" with options:

- **Components page** — Place the main component on the dedicated Components page.
- **Same page as usages** — Keep it on the page where its instances appear.

Do not proceed to Phase 5 until all selected patterns have answers.

### Mode B — Tokenize

Within the selected scope, call `get_design_context` and `get_variable_defs` to collect:

- All fill colors used (hex values and how many layers use each)
- All stroke colors used
- All font families, sizes, weights, and line heights used
- All spacing values (padding, gap) used in auto-layout frames

Present findings grouped by category:

```
Tokenization Findings
────────────────────────────────────────
Colors (fills + strokes)
  #1A1A2E — used in 34 layers   ← likely primary text
  #FF6B6B — used in 12 layers   ← likely accent/error
  ...

Typography
  Inter 16/24 Regular — used in 28 layers   ← likely body
  Inter 24/32 SemiBold — used in 14 layers  ← likely heading-md
  ...

Spacing
  16px gap — used in 18 auto-layout frames
  24px padding — used in 22 frames
  ...
────────────────────────────────────────
```

Ask:

1. "Which of these should become named tokens? (select all, or list by number)"
2. "Do you have a naming convention for tokens? (e.g. `color/primary/500`, `text/body`, `space/md`)"
3. "Should I create a new variable collection, or add to an existing one? (if existing: which one?)"

### Mode C — Retheme

Use `AskUserQuestion` (header: "Retheme") to ask "What is changing?" with options:

- **Colors** — Update the color palette only.
- **Typography** — Update the type scale only.
- **Both** — Update colors and typography.

Then collect the new values as plain free-text prompts (palettes, type scales, and font names are open-ended — not `AskUserQuestion`):

**If colors:** 2. "Paste the new color palette. For each color, give me: name, hex value, and what it replaces (or 'new')."
Accept formats like: `Primary: #2563EB (replaces #1A1A2E)` or a JSON/table. 3. "Are there semantic aliases to update? (e.g. `color/brand` should now point to `Primary` instead of `Accent`)"

**If typography:** 2. "Paste the new type scale: for each style, give me: name, font family, size, weight, line height." 3. "Are there any font family changes? (if yes: from which to which)"

After collecting the new values, scan the file for:

- Elements using variables → these will update automatically when variables are changed
- Elements with hardcoded values that match old colors/sizes → these need manual binding

Report the hardcoded elements:

```
Hardcoded elements that need binding (will not update automatically):
- [Frame name] / [Layer name]: fill #1A1A2E → should become color/primary
- ...
([N] total)
```

Then use `AskUserQuestion` (header: "Hardcoded") to ask "[N] hardcoded elements need binding. How should I handle them?" with options:

- **Apply automatically** — Bind all of them to the matching variables.
- **Review each** — Walk through them one at a time before binding.

### Mode D — Audit

No interrogation needed. Read the full file and identify:

1. **Detached components**: Frames/groups that visually match an existing main component but are not instances of it
2. **Hardcoded values**: Layers using fills/text styles not bound to a variable or style — especially if the same value appears elsewhere as a variable
3. **Naming violations**: Frames/layers using generic names (Frame, Group, Rectangle, Ellipse) at the top level
4. **Missing states**: Screens that exist in "default" state but have no error, empty, or loading state when one is expected (inferred from the interaction type)
5. **Orphaned components**: Main components with zero instances across the file
6. **Inconsistent spacing**: Auto-layout frames with padding/gap values that differ from the dominant spacing values used elsewhere

Present a prioritized fix plan:

```
Audit Results — [file name]
────────────────────────────────────────
🔴 High priority
  [N] detached components — [frame names]
  [N] hardcoded colors that conflict with existing tokens

🟡 Medium priority
  [N] naming violations in top-level frames
  [N] missing error/empty states

🟢 Low priority
  [N] orphaned components
  [N] spacing inconsistencies

────────────────────────────────────────
```

After showing the audit results, use `AskUserQuestion` with `multiSelect: true` (header: "Fix what?") to ask "What would you like to fix?" with options:

- **All findings** — Fix everything listed.
- **High priority only** — Fix just the 🔴 items.
- One option per finding category present (e.g. "Detached components", "Hardcoded colors", "Naming violations", "Missing states", "Orphaned components", "Spacing") so the user can cherry-pick.

(If the user only wants to review, they can decline the question / pick "Other" and say "just show me the list".)

Convert selected audit items into Componentize, Tokenize, or direct fix tasks, then proceed through the matching Mode A/B/C flow or Phase 5 directly.

---

## Phase 5 — Preview the Change Plan

Before executing anything in Figma, present a concrete plan of what will be created, modified, and replaced. The user must confirm before any writes happen.

```
Change Plan
────────────────────────────────────────
CREATE
  Component: [name] ([variant count] variants)
  Variable collection: [name] ([N] tokens)

MODIFY
  [N] variables updated: [list key ones]

REPLACE IN-PLACE
  [N] frames / layers will have instances swapped or values rebound

PAGES AFFECTED
  [page names]
────────────────────────────────────────
```

After showing the plan, use `AskUserQuestion` (header: "Change plan") to ask "Ready to execute this change plan in Figma?" with options:

- **Confirm** — Proceed to Phase 6 and execute the plan.
- **Adjust** — Change part of the plan first (the user describes what to adjust).
- **Cancel** — Stop without writing anything to Figma.

Do not proceed to Phase 6 until the user selects **Confirm**.

---

## Phase 6 — Execute in Figma

The change plan was already confirmed in Phase 5, so the Polish Agent runs as an autonomous **subagent on Fable** (`~/.claude/skills/quill/agents/polish-agent.md`) — structural Figma refactoring is the highest-risk work in Quill, so it gets the top tier. There is no further user gate inside this phase.

Dispatch the Polish Agent via the **Agent tool with `model: fable`**, passing:

- The mode (A / B / C / D)
- The confirmed change plan
- The scope (pages or frames)
- All answers from the interrogation

The subagent loads `figma-use` (and `figma-generate-library` for component/token work) itself before any `use_figma` call. It executes the changes and returns:

- List of created/modified Figma node URLs
- Summary of what was created vs. updated vs. replaced

If the subagent returns an **unresolved decision** instead of a result (e.g. a naming or variant choice the plan didn't cover), resolve it with the user — via `AskUserQuestion` for bounded choices, or a plain prompt for open-ended details — then re-dispatch the Polish Agent with the answer.

---

## Phase 7 — Check for Story Link Drift

If any top-level frames were renamed, moved to a different page, or deleted during Phase 6, those frames may be linked from Notion stories.

Search the active project's Notion stories database for stories whose "Figma Link" property points to a URL containing any of the affected node IDs.

For each affected story:

- Update the "Figma Link" property to the new node URL.
- Add a note in the story's "Open Questions" field: "Figma frame was restructured during UI polish on [date]."

Report how many stories were updated.

---

## Phase 8 — Update Notion Design System Spec

Check `notion.designSystemPage` in the active project config.

**If the field exists:** fetch the page and proceed to update it.

**If the field is absent:** use `AskUserQuestion` (header: "Design spec") to ask "Keep a Design System spec in Notion for this project? It documents components, tokens, and a changelog." with options:

- **Yes, create it** — Quill creates the Design System page and sub-databases and records this session.
- **Skip** — Don't track a design system spec in Notion.

If "Yes, create it":

- Use the Notion MCP to create a page called "[Product Name] — Design System" as a child of the stories page's parent.
- Create three sub-databases on that page:
  - **Components** — properties: Name (title), Figma Link (url), Description (text), Variants (text), Status (select: Active / Deprecated)
  - **Tokens** — properties: Name (title), Category (select: Color / Typography / Spacing / Radius / Shadow), Value (text), Figma Variable (text), Replaces (text)
  - **Changelog** — properties: Date (date), Change Type (select: Componentize / Tokenize / Retheme / Audit / Other), Summary (text), Affected Areas (text)
- Save the page URL to `notion.designSystemPage` in `quill.config.json` (update `projects[activeProject].notion.designSystemPage`).

**Updates to make (always):**

For **Componentize** sessions: add a row to Components for each new component (name, Figma link, description, variant list, Status: Active).

For **Tokenize** sessions: add a row to Tokens for each new token (name, category, value, Figma variable name).

For **Retheme** sessions: update existing Token rows with new values; add a Changelog entry summarizing the convention change and which areas were affected.

For **Audit** sessions: add a Changelog entry listing what was fixed and what remains open.

---

## Phase 9 — Confirm

Tell the user:

> "Polish complete for **[product.name]**:
>
> Figma
>
> - [N] components created/updated → [link to Components page in Figma]
> - [N] tokens created/updated
> - [N] frames updated
>
> Notion
>
> - Design System spec: [designSystemPage URL]
> - [N] components documented
> - [N] tokens documented
> - [N] stories updated with new Figma links
>
> Run `/quill polish-ui` again to continue polishing, or `/quill change-request` to handle a functional change."
