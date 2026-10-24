# Trackers

The project file's `tracker:` picks the column. Load a tool's schema (`ToolSearch`) before
the first call to it.

| Need | Linear (`mcp__claude_ai_Linear__*`) | Notion tasks database (`mcp__claude_ai_Notion__*`) | GitHub Issues (`gh`) |
|---|---|---|---|
| Fetch a ticket | `get_issue`, `list_comments` | `notion-fetch` on the page | `gh issue view <n> -R <repo> --comments` |
| Search | `list_issues` with keywords on the team | `notion-search` inside the database | `gh issue list -R <repo> --search "<words>" --state all` |
| Create | `save_issue` with every field at once | `notion-create-pages` with the database as parent, properties per the project file | `gh issue create -R <repo> --title … --body-file … --label …` |
| Update | `save_issue` with the id | `notion-update-page` | `gh issue edit <n> -R <repo> --body-file …` |
| Comment | `save_comment` | `notion-create-comment` | `gh issue comment <n> -R <repo> --body-file …` |
| Parent / sub-ticket | `parentId` on `save_issue` | the parent relation property | a sub-issue, or a task list in the parent's body |
| Blocked-by / related / duplicate | relation fields on `save_issue` | the relation properties the database has | a "Blocked by #n" line in the body; close as duplicate with `gh issue close <n> --reason "not planned"` and a comment linking the survivor |
| Estimate | the `estimate` field | the estimate property, if any | the description's **Estimate** section |

## Learn a project

Read-only, to build the project file:
- **Linear:** `list_teams` (the team), `list_issue_labels` on the team, `list_issue_statuses`,
  and `list_issues` on the team (five recent, with estimates) to see the estimate scale in use.
- **Notion:** `notion-fetch` on the database for its property names, status options and
  estimate property; `notion-query-data-sources` for five recent tasks.
- **GitHub:** `gh label list -R <repo>`, `gh issue list -R <repo> --limit 5 --state all`.

Write long bodies to a file in the scratchpad and pass the file (`--body-file`), never a
quoted shell string. Markdown goes to Linear and Notion with real newlines, not `\n`.
