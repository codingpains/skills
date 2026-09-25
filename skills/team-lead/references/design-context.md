# Design context

Tickets with a user-facing change often carry a design: Figma links, screenshots
pasted into the ticket, a prototype folder in the repo, or a Notion design
requirements page. The Lead collects them once at intake into a **design brief**;
every agent that plans, builds, tests or reviews UI works from it and checks its
output against it.

## Where designs hide

Collect every one of these the ticket reaches:

- Figma URLs anywhere in the ticket: description, comments, attachments, and
  the linked Notion pages. `figma.com/design/<fileKey>/<name>?node-id=<a>-<b>`
  (also `/file/`, `/proto/`, `/board/`). The node ID is `node-id` with the dash
  turned into a colon: `19697-226156` → `19697:226156`. A URL without
  `node-id` points at the whole file: ask which frames matter only if the file
  is large and nothing else in the ticket narrows it.
- Images pasted into the ticket (`<linear-image>` in a Linear description,
  `attachments` in its comments, images in a Notion page).
- A design or prototype folder in the repo that the ticket or the repo profile
  names (in megalith: `designs/<project>/`).
- A Notion "Design Requirements" page under the ticket's epic.
- When the ticket changes UI but carries no design, its **parent** issue or
  epic, and the ticket's linked PRD: children often inherit the epic's frames.

A later comment beats the description, and a decision from design or product
beats the picture. Record which source wins for each disputed point.

## Figma access

Figma is read through an MCP server. Find what this session has with
`ToolSearch` query `figma get_design_context get_screenshot`. Two servers can
provide it, with the same tool names:

| Server | Tool prefix | Needs |
|---|---|---|
| Figma desktop app (the Quill plugin's `figma`) | `mcp__plugin_quill_figma__` | the Figma desktop app running with its MCP server enabled (Preferences → Enable Dev Mode MCP server), and the file open in it |
| Figma remote (claude.ai connector) | `mcp__claude_ai_Figma__` | the Figma connector authorized in claude.ai |

The tools: `get_screenshot` (an image of a node), `get_design_context` (the
node's structure and suggested code, with its text), `get_metadata` (the layer
tree: names, sizes, positions; cheap, use it to find the right frames in a big
node), `get_variable_defs` (the design tokens the node uses).

When neither server answers, ask the human (`AskUserQuestion`): open the Figma
desktop app with the file and its MCP server on, then retry (recommended);
continue with the ticket's images only; or stop. Never build a UI from a
paraphrase of a design nobody could open; say what was missing in the brief.

**Keep designs private.** Never upload a design image or export anywhere:
not to Planbin (`npx planbin file` makes a public URL), not to a PR, not to
Slack. The brief and its images stay in the run directory. The plan links to
Figma by URL and node ID.

## The brief

`<run dir>/design/design.md`, with the images beside it:

```
# Design brief — <TICKET_ID>

## Sources
| # | Source | Link / path | Node | What it shows | Wins over |
|---|---|---|---|---|---|
| D1 | Figma | <url> | 19697:226156 | Publish modal, rollout = Progressive | — |
| D2 | Ticket image | design/linear-1.png | — | Same modal, older copy | D1 wins (newer) |

## Screens and states
One block per screen or state: what is on it, top to bottom. Every visible
string verbatim, in quotes. Components (buttons, banners, inputs, tables,
modals), their variants and disabled/error/empty/loading states. Layout:
alignment, grouping, spacing where it is explicit. Which state follows which
interaction.

## Tokens
Colors, type styles, spacing and radii from `get_variable_defs`, by token name.

## Behavior the design implies
Rules the pictures encode, phrased as testable statements: "the warning text
changes with the selected rollout option", "Save draft appears only for ...".
Each one either maps to an acceptance criterion or is flagged as new.

## Gaps
States or cases the design does not show (errors, empty, long text, mobile).
Each is a question for grooming or a decision for the Architect.
```

Images: download ticket images right away (`curl -sfL -o <run dir>/design/<name>.png "<url>"`;
Linear's signed URLs expire after about five minutes, so re-fetch the issue if
one fails). Figma screenshots come back inside the tool result, not as files;
agents fetch their own with `get_screenshot` when they compare. If a
`FIGMA_TOKEN` environment variable is set, also export each frame to a file
every agent can open without the MCP server:

```sh
curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/images/<fileKey>?ids=<node-id>&format=png&scale=2" \
  | python3 -c 'import json,sys; print(next(iter(json.load(sys.stdin)["images"].values())))' \
  | xargs curl -sfL -o <run dir>/design/<D#>.png
```

## How each agent uses it

- **Architect**: reads the brief, looks at every source, and maps each screen
  and state to components, preferring the repo's design system (the profile's
  *UI* section names it). The plan gets a *UI* section: per screen/state, the
  component to reuse or build, props and variants, the copy, the tokens, and
  the behavior rules. Design gaps are decisions scored like any other.
- **Coder**: builds each screen to the brief: structure, copy verbatim,
  states, tokens. When the profile gives a way to render the UI, renders the
  changed component in each designed state, captures it, and compares it with
  the design side by side. Fixes what differs before committing.
- **Hardener**: keeps the rendering identical while refactoring; when a
  render path exists, captures before and after.
- **Tester**: turns *Behavior the design implies* into tests: every state and
  every copy change the design ties to an input.
- **Reviewer**: checks conformance itself, from the design sources and, when
  a render path exists, a fresh capture. A difference is a finding: must-fix
  when it breaks an acceptance criterion or a designed state, should-fix for
  visible drift, nit for pixel noise.
- **Wrap-up coder**: re-captures any screen a fix touches.

Every agent that touched UI adds this to its report under *Stage-specific*:

```
Design conformance:
| Screen / state | Source | Matches | Difference, and why |
|---|---|---|---|
| Publish modal, Progressive | D1 | yes | — |
| Publish modal, Full restart | D1 | no | banner copy differs: design text is older than the comment on <date> |
Captures: <paths, or "no render path: compared by reading the code">
```
