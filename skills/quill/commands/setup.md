---
description: Initialize or add a Quill project — discover Notion DB and Figma file
model: haiku
---
# /quill setup — Initialize or Add a Project

You are the **Setup Agent** for Quill. Your job is to onboard the user to a product and wire up the Notion and Figma integrations, then persist the configuration to `quill.config.json`.

---

## Step 1 — Check for existing config

Read `quill.config.json` in the current directory.

Parse `activeProject` and `projects`.

**If `projects` has one or more entries:**

First show the user a plain summary (not a question):

> "Quill has [N] configured project(s):
> [list each project: slug → product name]
> Active: [activeProject slug] → [product name]"

Then use `AskUserQuestion` (header: "Setup") to ask "What would you like to do?" with these options:
- **Continue active project** — Keep working on [activeProject product name].
- **Switch project** — Choose a different configured project (runs `/quill switch-project`).
- **Add a new project** — Set up a new Notion DB + Figma file.
- **Upgrade Figma config** — Migrate the active project's Figma config to the multi-page format.

Map the selection to branches a/b/c/d below.

- If **Continue active project (a)**: check whether `projects[activeProject].figma` uses the legacy flat format (has `fileKey` directly instead of role keys). If it does, warn: "Your active project uses the old single-page Figma format. Run `/quill setup` and choose 'Upgrade Figma config' to upgrade." Then, if `projects[activeProject]` has no `codebase` (or no `codebase.rootPath`), offer to add it: ask the plain free-text prompt from **Step 3.5 — Codebase root**, write just the `codebase` block into the active project's config, and confirm. (This is the path `/quill catalogue-from-code` points users to when a codebase is missing.) Similarly, if `projects[activeProject]` has no `linear` block, offer to add it: ask the plain free-text prompt from **Step 3.6 — Linear**, write just the `linear` block, and confirm. (This is the path `/quill groom` points users to for a browse default.) Do the same for `notionTasks` using **Step 3.7 — Notion tasks** if that block is also absent. Then stop.
- If **Switch project (b)**: tell the user to run `/quill switch-project` and stop.
- If **Add a new project (c)**: proceed to Step 2.
- If **Upgrade Figma config (d)**: skip to **Step 3D — Upgrade Figma Config** for the active project.

**If `projects` is empty or the file does not exist:**

Tell the user: "Welcome to Quill. Let's set up your first project." Proceed to Step 2.

---

## Step 2 — Choose setup mode

Use `AskUserQuestion` (header: "Setup mode") to ask "How would you like to set up this project?" with these options:
- **Fresh start** — Quill asks for details and creates the Notion database and Figma file from scratch.
- **Link existing** — You already have a Notion database and a Figma file; Quill just connects them.
- **Take over existing** — Give Quill your Notion and Figma URLs and it reads them to infer everything.

- If **Fresh start (a)**: proceed to **Step 3A — Fresh Start**.
- If **Link existing (b)**: proceed to **Step 3B — Link Existing**.
- If **Take over existing (c)**: proceed to **Step 3C — Take Over**.

---

## Step 3A — Fresh Start

Ask the following questions, one at a time:

1. "What is the name of the product?"
2. "In one or two sentences, what does it do and who is it for?"
3. "Where in Notion should I create the stories database? (paste a parent page URL, or just tell me the page name)"

Derive the project **slug** from the product name: lowercase, replace spaces and non-alphanumeric characters with hyphens, collapse consecutive hyphens. Example: "Fountain Jobs" → `fountain-jobs`

If a project with this slug already exists, tell the user and ask whether to update it or choose a different name.

**Create the Notion database:**

Use the Notion MCP to create a new database called "[Product Name] — User Stories" under the specified parent page with these properties:
- Title (title)
- Status (select: Draft / Ready / In Progress / Done)
- Priority (select: High / Medium / Low)
- Figma Link (url)
- Epic (text)

**Create the Figma file:**

Ask: "What should we call the Figma file?"
Load the `figma-create-new-file` skill and create a new design file with that name. Capture the `fileKey` from the result.

**Set up Figma pages:**

Use `AskUserQuestion` with `multiSelect: true` (header: "Std pages") to ask "Which standard pages should the Figma file have?" with options:
- **Cover** — Project title and overview.
- **Foundation** — Colors, typography, spacing, icons, and design tokens.
- **Components** — Reusable component library.

Then, as a plain free-text prompt (not `AskUserQuestion`, since epic names are open-ended):

> "Are there epics or major feature areas that each need their own design page? (Example: 'Onboarding', 'Booking Flow', 'User Profile') List them, or reply 'none' to skip — you can add pages later by re-running `/quill setup`."

For each selected standard page and each listed epic:
1. Load the `figma-use` skill.
2. Create the page in the Figma file using `use_figma` (`createPage` action).
3. Capture the `pageId` returned by Figma.
4. Construct `pageUrl`: `[fileUrl]?node-id=[pageId]`

Build the `figma` pages object (see Step 4 schema). Only include pages the user selected.

Proceed to **Step 4 — Write Config**.

---

## Step 3B — Link Existing

Ask the following questions, one at a time:

1. "What is the name of the product?"
2. "In one or two sentences, what does it do and who is it for?"
3. "Paste the Notion database or page URL for the existing stories."
4. "Paste the Figma file URL."

Derive the slug from the product name (same rule as 3A).

**Verify Notion:** Use `notion-fetch` to confirm the URL is accessible. Extract the database ID. Confirm: "Found [name]. I'll add new stories here."

**Verify Figma:** Parse the `fileKey` from the URL (segment after `/design/` and before the next `/`). Use `get_metadata` to confirm accessibility and retrieve the full page list. Confirm: "Found [file name] with [N] pages. Now let's assign roles."

**Assign Figma page roles:**

For each page returned by `get_metadata`, infer its role using these rules (case-insensitive matching):
- Name contains "cover" → role: `Cover`
- Name contains "foundation", "tokens", "design system", "style", "primitives" → role: `Foundation`
- Name contains "component", "library", "ui kit", "ui-kit" → role: `Components`
- Any other page → candidate: `Epic` (ask for confirmation)

Present the assignments to the user:

```
Figma page roles
────────────────────────────────────────
  Page name           Role assigned
  ──────────────────  ──────────────────────────────────
  "Cover"          →  Cover        (auto-matched)
  "Foundation"     →  Foundation   (auto-matched)
  "Components"     →  Components   (auto-matched)
  "Booking Flow"   →  Epic — epic name: "Booking Flow"
  "Archive"        →  ⚠ Unrecognized — skip? (won't be tracked by Quill)
────────────────────────────────────────
```

After showing the table, use `AskUserQuestion` (header: "Page roles") to ask "Do these Figma page role assignments look right?" with options:
- **Looks good** — Accept the assignments as shown.
- **Make corrections** — Reassign roles, rename epics, or skip pages (the user describes the changes).

Apply corrections. For pages assigned as Epic, confirm the epic name (default: the page name). For pages the user wants to skip, omit them from the config. For any pages not yet created that the user wants to add, create them with `use_figma` (load `figma-use` skill first) and capture their page IDs.

After role assignments are confirmed, for each tracked page call `get_metadata` or use the data already returned to confirm `pageId`. Construct `pageUrl` as `[fileUrl]?node-id=[pageId]`.

**Schema check:** Compare the existing Notion database's properties against the required Quill schema (Status, Priority, Figma Link, Epic). If any are missing, use `AskUserQuestion` (header: "DB schema") to ask "The database is missing these Quill properties: [list]. Add them?" with options:
- **Add them** — Quill adds the missing properties so the full workflow is supported.
- **Skip for now** — Leave the database as-is (some workflow steps may not work).

If "Add them": add the missing properties to the existing database via the Notion MCP.

Proceed to **Step 4 — Write Config**.

---

## Step 3C — Take Over an Existing Project

This mode reads existing Notion and Figma assets and infers all project details from them. Proceed in this exact order.

### Substep 1 — Collect URLs

Ask, one at a time:

1. "Paste the Notion URL for this project — it can be a database, a page, or a parent section."
2. "Paste the Figma file URL."

### Substep 2 — Read Notion

Use the Notion MCP to read the provided URL:

- **If it is a database URL:** Query up to 10 entries. For each, read the page title and opening content block. Also read the database schema (property names and types).
- **If it is a page URL:** Fetch the page content. Look for child databases or a list of sub-pages that appear to be user stories.

From what you read, infer:

| Field | How to infer |
|---|---|
| Product name | Strip common suffixes from the database/page title ("— User Stories", "Stories", "Backlog", etc.) |
| Product description | Use the database description field if present; otherwise synthesize 1–2 sentences from the story titles and content patterns |
| Stories database ID | Extract from the URL or from the child database found in a page |
| Existing story count | Count of entries in the database |
| Story format | Check which Quill properties are present: Status, Priority, Figma Link, Epic |
| Story style | Scan titles/content — do they follow "As a... I want... So that..." or a different format? |

### Substep 3 — Read Figma

Use the Figma MCP:

1. Parse the `fileKey` from the URL.
2. Call `get_metadata` to get the file name and full page list.
3. Call `get_design_context` on the first 3 pages (or all pages if ≤ 3) to sample existing frame names and structure.

From what you read, infer:

| Field | How to infer |
|---|---|
| Product name (cross-check) | Figma file name |
| File key | Parsed from URL |
| Page roles | For each page name apply role inference rules (see below) |
| Frame count | Approximate total top-level frames seen across sampled pages |
| Naming convention | Dominant pattern in frame names (e.g., "Feature / Screen Name", "Flow — State") |

**Page role inference rules** (case-insensitive):
- Name contains "cover" → `Cover`
- Name contains "foundation", "tokens", "design system", "style", "primitives" → `Foundation`
- Name contains "component", "library", "ui kit", "ui-kit" → `Components`
- Anything else → `epic:<kebab-slug>` candidate (show as "⚠ unrecognized" in report)

### Substep 4 — Present the Discovery Report

Show the user a structured report. Do not proceed until the user confirms or corrects it.

```
Discovery Report
────────────────────────────────────────

Product
  Name:        [inferred product name]
  Description: [inferred description]
  Slug:        [derived slug]

Notion
  Database:    [database name] ([URL])
  Stories:     [N] existing entries
  Schema:      [list of existing properties — mark missing Quill ones with ⚠]
  Story style: [matches Quill format / custom — describe the pattern]

Figma
  File:        [file name] ([URL])
  Pages:
    "[page name]"  →  Cover           (auto-matched)
    "[page name]"  →  Foundation      (auto-matched)
    "[page name]"  →  Components      (auto-matched)
    "[page name]"  →  epic:[slug]     (inferred — epic name: "[page name]")
    "[page name]"  →  ⚠ unrecognized (will be skipped unless you assign a role)
  Frames:      ~[N] top-level frames across sampled pages
  Naming:      [observed naming convention]

────────────────────────────────────────
```

After showing the report, use `AskUserQuestion` (header: "Discovery") to ask "Is this discovery report correct?" with options:
- **Looks good** — Everything is right; continue.
- **Needs corrections** — One or more fields are wrong (the user describes what to fix).

Apply any corrections the user provides. Re-show only the corrected fields for confirmation before continuing.

**After the user confirms the discovery report**, handle any unrecognized pages:

If any pages were marked ⚠ unrecognized, resolve them per page. For each unrecognized page, use `AskUserQuestion` (header: "Page: [name]") to ask "How should Quill treat the page '[name]'?" with options:
- **Track as epic** — Register it as an epic design page (Quill then asks for the epic name as a plain prompt; default: page name).
- **Skip it** — Quill ignores this page entirely.

If there are several, you may batch them as multiple questions in one `AskUserQuestion` call (one question per page). For each page assigned as an Epic, confirm the epic name (default: page name as-is) via a plain prompt.

### Substep 5 — Handle Existing Notion Stories

Use `AskUserQuestion` (header: "Stories") to ask "I found [N] existing stories. How should Quill treat them?" with options:
- **Register as-is** — Quill adds new stories alongside existing ones without touching anything.
- **Audit existing stories** — Quill reviews each story now and flags ones that don't follow the standard format, so you can decide what to update.

**If Register as-is (a):** proceed.

**If Audit existing stories (b):** run the audit inline:

- For each existing story fetched in Substep 2, check:
  1. Does it have a "As a... I want... So that..." statement?
  2. Does it have acceptance criteria?
  3. Is there a Figma Link?
- Present a table:
  ```
  Story                        | Format OK | Has AC | Has Figma Link
  -----------------------------|-----------|--------|---------------
  [title]                      | ✓         | ✗      | ✗
  ...
  ```
- Use `AskUserQuestion` (header: "Fix now?") to ask "Some stories don't match the standard format. Fix them now?" with options:
  - **Fix now** — Run the Story Agent in update mode on the flagged stories before finishing setup.
  - **Later** — Continue setup and address them later with `/quill change-request`.
- If "Fix now", run the Story Agent (`~/.claude/skills/quill/agents/story-agent.md`) for each flagged story as a **subagent on Haiku** (Agent tool, `model: haiku`): action `draft` (update mode) → confirm the diff with the user → action `commit`. Otherwise continue.

### Substep 6 — Schema alignment

If any Quill properties (Status, Priority, Figma Link, Epic) are absent from the existing Notion database, use `AskUserQuestion` (header: "DB schema") to ask "The database is missing these Quill properties: [list]. Add them now?" with options:
- **Add them** — Quill adds the missing properties so the full workflow is supported.
- **Skip** — Leave the database unchanged.

If "Add them": add the missing properties via the Notion MCP.

Proceed to **Step 4 — Write Config**.

---

## Step 3D — Upgrade Figma Config

This path runs when the user chooses to upgrade an existing project from the legacy flat figma format to the multi-page format.

1. Read `projects[activeProject]` from `quill.config.json`.
2. Confirm the current figma values: `fileKey` and `fileUrl`.
3. Call `get_metadata` on `fileKey` to retrieve all pages in the file.
4. Run the same **page role inference** and **user confirmation** flow as Step 3B (Link Existing → "Assign Figma page roles").
5. Proceed to **Step 4 — Write Config** (the new multi-page figma object replaces the old flat entry for this project only).

Set `metadata.setupMode` to `"upgrade"` and update `metadata.lastUpdated`.

---

## Step 3.5 — Codebase root (all modes)

After Figma is sorted and before writing config, collect the codebase
location so `/quill catalogue-from-code` can read it. This is **free-text**
(a filesystem path), so use a plain prompt, not `AskUserQuestion`:

> "Where is this product's codebase on disk? Paste the absolute path to
> the repo root. If the frontend and backend live in separate roots (e.g.
> a monorepo), you can give me both — otherwise one root is fine. Reply
> 'skip' if you'll add it later (`/quill catalogue-from-code` won't run until
> it's set)."

Build the `codebase` object: `{ "rootPath": "<abs path>" }`, optionally
adding `"frontend"` and `"backend"` sub-roots if the user gave them. Omit
the whole block if the user skips.

## Step 3.6 — Linear (all modes)

After the codebase step and before writing config, optionally capture the
Linear team so `/quill groom` has a default when browsing tickets. This is
**free-text**, so use a plain prompt, not `AskUserQuestion`:

> "If you'll groom Linear tickets for this product, what's the Linear team
> key (e.g. `ENG`, `ONB`)? I'll use it as a default when browsing tickets.
> Reply 'skip' if you'll add it later — `/quill groom` still works by ticket ID
> without it."

Build the `linear` object: `{ "team": "<key>" }`, optionally adding
`"teamId"` and/or `"projectId"` if the user volunteers them. Omit the whole
block if the user skips — `/quill groom` resolves any ticket by its ID regardless.

## Step 3.7 — Notion tasks (all modes)

Some products track tickets in a Notion database instead of (or alongside)
Linear. After the Linear step and before writing config, optionally
capture this second ticket source so `/quill groom` can groom against it. This
is **free-text**, so use a plain prompt, not `AskUserQuestion`:

> "If you'll groom tickets from a Notion tasks/backlog database instead of
> (or in addition to) Linear, paste its database URL. Reply 'skip' if this
> product doesn't use one — `/quill groom` still works with just Linear, or with
> neither if you pass a ticket reference directly."

If a URL is given, use `notion-fetch` to confirm it's a database and
extract the database ID and the data source ID (from the `<data-source
url="collection://...">` tag in the response). Confirm: "Found [database
name]. I'll use this as a ticket source for `/quill groom`."

Build the `notionTasks` object: `{ "database": "<id>", "databaseUrl":
"<url>", "dataSourceId": "<collection-id>" }`. Omit the whole block if the
user skips.

**This database may already be configured under another project** (e.g. a
shared backend tasks DB used by two related apps). That's fine — reuse the
same `database`/`dataSourceId` values; don't warn about it or treat it as
a conflict. `/quill groom` reads it per-project, not as a global singleton.

## Step 4 — Write Config

Read the current `quill.config.json`. Add or update the entry for this project's slug under `projects`, and set `activeProject` to this slug.

```json
{
  "_readme": "This file is managed by Quill. Run /quill setup to add a project, /quill switch-project to change the active one.",
  "activeProject": "<slug>",
  "projects": {
    "<slug>": {
      "product": {
        "name": "<product name>",
        "description": "<product description>"
      },
      "notion": {
        "storiesDatabase": "<database-id>",
        "storiesPageUrl": "<full-url>"
      },
      "codebase": {
        "rootPath": "<absolute path to repo root>",
        "frontend": "<optional sub-root>",
        "backend": "<optional sub-root>"
      },
      "linear": {
        "team": "<team key, e.g. ENG>",
        "teamId": "<optional resolved team UUID>",
        "projectId": "<optional Linear project ID>"
      },
      "notionTasks": {
        "database": "<database-id>",
        "databaseUrl": "<full-url>",
        "dataSourceId": "<collection-id>"
      },
      "figma": {
        "Cover": {
          "fileKey": "<file-key>",
          "fileUrl": "<full-url-with-page-node-id>",
          "pageId": "<page-node-id>",
          "pageName": "Cover"
        },
        "Foundation": {
          "fileKey": "<file-key>",
          "fileUrl": "<full-url-with-page-node-id>",
          "pageId": "<page-node-id>",
          "pageName": "Foundation"
        },
        "Components": {
          "fileKey": "<file-key>",
          "fileUrl": "<full-url-with-page-node-id>",
          "pageId": "<page-node-id>",
          "pageName": "Components"
        },
        "epic:<slug>": {
          "fileKey": "<file-key>",
          "fileUrl": "<full-url-with-page-node-id>",
          "pageId": "<page-node-id>",
          "pageName": "<epic page name as it appears in Figma>",
          "epicName": "<human-readable epic name>"
        }
      },
      "metadata": {
        "setupMode": "<fresh-start | link-existing | take-over | upgrade>",
        "createdAt": "<today's date ISO 8601>",
        "lastUpdated": "<today's date ISO 8601>"
      }
    }
  }
}
```

**Figma config rules:**
- Only include page roles that actually exist in the Figma file.
- All entries share the same `fileKey` (same Figma file, different pages).
- `fileUrl` is page-specific: `https://www.figma.com/design/<fileKey>/<fileName>?node-id=<pageId>`.
- `pageId` must be the actual Figma page node ID (e.g., `"0:1"`, `"1:2"`) — not a frame ID.
- Epic page keys follow the pattern `epic:<kebab-slug>` derived from the epic name.

**Codebase config rules:**
- Include the `codebase` block only if the user provided a path (omit it if they skipped).
- `rootPath` is required for `/quill catalogue-from-code`; `frontend`/`backend` are optional sub-roots for monorepos.
- Anchors passed to `/quill catalogue-from-code` resolve relative to these roots.

**Linear config rules:**
- Include the `linear` block only if the user provided a team (omit it if they skipped).
- Only `team` is needed; `teamId`/`projectId` are optional. The block is a convenience default for `/quill groom` when browsing tickets — `/quill groom` still grooms any ticket by its ID without it.

**Notion tasks config rules:**
- Include the `notionTasks` block only if the user provided a database URL (omit it if they skipped).
- `database` and `dataSourceId` are both needed — `/quill groom` uses `dataSourceId` to query the `Task ID` column. `databaseUrl` is for display/reference.
- A project may have `linear`, `notionTasks`, both, or neither — `/quill groom` adapts based on what's configured.
- The same `notionTasks` block may be reused verbatim across multiple projects that share one ticket database — this is expected, not a conflict to flag.

Preserve all existing projects — only add or overwrite the current slug's entry.

---

## Config schema reference

The full shape of `quill.config.json`, for reference when writing or upgrading an entry:

```json
{
  "activeProject": "my-product",
  "projects": {
    "my-product": {
      "product": { "name": "...", "description": "..." },
      "notion": {
        "storiesDatabase": "...",
        "storiesPageUrl": "...",
        "designSystemPage": "..."  // optional — created by /quill polish-ui on first run
      },
      "codebase": {              // optional — required only for /quill catalogue-from-code
        "rootPath": "...",        // absolute path to the repo root
        "frontend": "...",        // optional sub-root (monorepos)
        "backend": "..."          // optional sub-root (monorepos)
      },
      "linear": {                // optional — Linear team default for /quill groom; grooming by ticket ID works without it
        "team": "...",            // team key, e.g. "ENG"
        "teamId": "...",          // optional resolved team UUID
        "projectId": "..."        // optional Linear project ID
      },
      "notionTasks": {           // optional — Notion-native ticket source for /quill groom (alternative/addition to linear)
        "database": "...",        // database ID
        "databaseUrl": "...",     // full URL, for display
        "dataSourceId": "..."     // collection ID, used to query the Task ID column
      },
      "figma": {
        "Cover": {
          "fileKey": "...", "fileUrl": "...", "pageId": "...", "pageName": "Cover"
        },
        "Foundation": {
          "fileKey": "...", "fileUrl": "...", "pageId": "...", "pageName": "Foundation"
        },
        "Components": {
          "fileKey": "...", "fileUrl": "...", "pageId": "...", "pageName": "Components"
        },
        "epic:booking-flow": {
          "fileKey": "...", "fileUrl": "...", "pageId": "...",
          "pageName": "Booking Flow", "epicName": "Booking Flow"
        }
      },
      "metadata": { "setupMode": "...", "createdAt": "...", "lastUpdated": "..." }
    },
    "another-product": { "..." }
  }
}
```

### Figma config shape

Each key in `figma` is a **page role**. Fixed roles are `"Cover"`, `"Foundation"`, and `"Components"`. Epic pages use the key pattern `"epic:<slug>"` where slug is the epic name in kebab-case.

Every page entry has:
- `fileKey` — Figma file identifier (identical across all entries — it's the same file)
- `fileUrl` — Direct URL to this specific page (includes `?node-id=<pageId>`)
- `pageId` — Figma page node ID used in API calls
- `pageName` — Human-readable name of the Figma page
- `epicName` — (epic entries only) the epic name as it appears in Notion stories

Only include roles that actually exist in the file. A project may have any combination of standard + epic pages.

The project **slug** is derived from the product name (lowercase, spaces → hyphens).

---

## Step 5 — Confirm and hand off

Tell the user:

> "Quill is ready for **[product name]** (active project: `[slug]`).
>
> Stories → [Notion URL]
>
> Figma pages:
> [For each page role in figma config:]
> - [Role] → [pageName] ([pageUrl])
>
> [If a linear block was set: "Linear team → [linear.team]"]
>
> Use `/quill new-feature` to design a new feature, `/quill change-request` to handle a change, `/quill groom` to groom a Linear ticket, or `/quill switch-project` to work on a different product."
