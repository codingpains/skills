# Project file

One file per project holds everything that differs between projects: the tracker and its
labels, the estimate scale, the repo, the test environment, the check command, the record IDs
evidence is built on, and the domain words that tripped earlier tickets. It lives in
`~/.ticket/projects/<KEY>.md`, outside the skills repo, because it names customers, people and
internal systems. Hand edits are welcome; keep `updated:` current.

`<KEY>` is:
- Linear: the team key (`ABC`).
- Notion tasks database: `notion-<first 8 characters of its data source id>`.
- GitHub Issues: `gh-<owner>-<repo>`.

The same keys as `/solo-groom`'s profiles in `~/.solo-groom/projects/`, so one project has one key.

## Finding it

Take the first that applies:
1. A ticket ID or URL in the request: its team key, database or repo.
2. Gustavo names the team or project.
3. The current directory is in a git repo: the project file whose `repos:` lists that remote
   (`git remote get-url origin`).
4. Exactly one project file exists: use it, and say so.

Nothing fits, or two do: ask once, listing the project files there are, plus "a new one".

## Format

```
---
key: ABC
tracker: linear            # linear | notion | github
team: Acme Core            # Linear team name, Notion database name, or owner/repo
repos:                     # remotes, so step 3 above can match; and the local checkout
  - github.com/acme/app  /Users/me/src/app  (default branch main; folders the team owns)
updated: 2026-10-23
---

## Tracker
<labels per ticket type: always / backend / frontend / bug / research / QA / groomed.
Priority scale. Estimate scale and its field (points, T-shirt, none → in the description).
States: backlog, to do. Default assignee for agent-bound tickets. For Notion: the property
names for title, status, estimate, labels, parent, and the status that means groomed.>

## Coding agent
<who picks up agent-ready tickets (a named agent, or "none"), and how a ticket is handed to it.>

## Evidence
<the record IDs a claim is built on (e.g. account / order / user), where read-only
production data lives (an analytics skill, a database replica, Sentry project), and the
test environment acceptance criteria name, with how a test account is found there.>

## Conventions
<check command a ticket's How to test names; test frameworks per area; feature flag naming
and where flags are defined; the repo's ticket template path, when it has one; writing rules
the repo keeps.>

## Domain notes
<one line each: a term people use → the exact name in code (with its path); the code path
most users run when a newer one exists; words the tracker auto-links; neighbouring teams and
how their conventions differ. Grows every run.>
```

Leave a section out rather than guess. An unknown test environment or record ID is written
as unknown, not invented.

## Building one

When no file matches, build it before writing, from what the machine already knows. Each
source is optional; skip what does not exist.

1. **The tracker**, read-only (`trackers.md` § Learn a project): labels, states, priorities,
   the estimate scale, and five recent tickets for their shape and length.
2. **`/solo-groom`'s profile** for the same key (`~/.solo-groom/projects/<KEY>.md`): its Tracker,
   Conventions and Glossary.
3. **Quill's config** (`$QUILL_HOME/quill.config.json`, else `~/.quill/quill.config.json`): the
   project whose `linear.team` or `notionTasks.dataSourceId` matches, for the product name and
   the codebase path.
4. **Team-lead repo profiles** (`~/.team-lead/repos/*.md`) whose `remote` matches the repo: the
   check command and test frameworks.
5. **The repo**: a ticket template (search `.claude/` and `docs/` for `ticket-template`), the
   check script (`package.json` scripts, `Makefile`, CI workflow), where feature flags are
   defined.

Write the file, then say in the report that it was created and where. Ask only what blocks
this ticket (Step 2): the rest stays unknown until a run learns it.

## After a run

Edit the file when the run learned something it lacked or got wrong: a label that exists, an
estimate scale, a corrected domain term, a word that auto-linked, the test environment.
Correct a wrong line rather than add a second one. Bump `updated:`. Keep it under about 80
lines.
