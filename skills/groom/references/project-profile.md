# Project profile

A profile records, for one project, where a groom finds its answers: the
repo, the docs, the tracker, the channels, the data, the words the code
uses, and what worked on earlier grooms. `/groom` reads it at intake and
updates it after every run, so each groom of the same project asks fewer
questions than the last.

Profiles live in `~/.groom/projects/<KEY>.md`, outside the skills repo:
they name customers, channels and internal pages. `<KEY>` is the Linear
team key (`ONB`, `I9C`) or, for a Notion tasks database, `notion-<first 8
characters of its data source id>`. Hand edits are welcome; keep
`updated:` current.

## Format

```
---
key: ONB
product: Onboard
updated: 2026-10-23
---

## Code
<one line per repo: absolute path of the main checkout, default branch, the
folders the team owns, and the team-lead repo profile that applies
(`~/.team-lead/repos/<name>.md`), when there is one. A researcher reads
code here, on the default branch, never in a worktree with a ticket's
changes.>

## Docs
<Notion pages a ticket leans on: the product page, the epics or PRDs
database, design requirements pages, the Quill stories database. One line
each: name, URL, what it answers.>

## Tracker
<Linear team and its labels, estimate scale and priorities, or the Notion
tasks database and its properties. The template the team's tickets follow,
when the repo has one (`.claude/skills/ticket-tree/references/ticket-template.md`
in megalith, for example). Statuses that mean groomed.>

## Conversations
<Slack channels where this product's problems and decisions are discussed,
with ids. Who decides what, when the ticket names people.>

## Production evidence
<where read-only records live: the `/investigate` skill's project profile
(`sources.md` and `domain.md` in `$INVESTIGATIONS_HOME/projects/<name>/`,
else `~/.investigations/projects/<name>/`) when one exists, the analytics
skills that query this product's data (`fountain-analytics:*`), Sentry
projects, the environments tickets name
(`dev-09`) and how a test company is found there.>

## Conventions
<feature flag naming and where flags are defined; how acceptance criteria
name environment, company and flag state; the repo's writing rules a
ticket must respect; the test frameworks each area uses, so a testing plan
names real ones.>

## Glossary
<one line per term: what the ticket or a human calls it → the exact
collection, field, setting or type name in code, with the path that proves
it. Grows every run.>

## Learned
<one line per entry, newest first, at most 40 lines:
`<date> <kind of question> → <source> (<what it gave>)`. A source that
answered the same kind twice gets one line with the latest date.>

## Dead ends
<sources that were searched for a kind of question and had nothing, so the
next groom skips them: `<date> <kind> ✗ <source> (<why>)`.>
```

## Building one

When `~/.groom/projects/<KEY>.md` does not exist, build it before the
audit, from what the machine already knows. Send the discovery to one
`general-purpose` agent on sonnet, so the config files and tool results
stay out of your context, and have it write the file:

1. **Quill's config** (`$QUILL_HOME/quill.config.json`, else
   `~/.quill/quill.config.json`): the project whose `linear.team` is the
   key, or whose `notionTasks.dataSourceId` matches. Take `product`,
   `codebase.rootPath` with its `frontend` and `backend` folders,
   `notion.storiesDatabase` and `notion.productPageUrl`.
2. **Team-lead repo profiles** (`~/.team-lead/repos/*.md`): the ones whose
   `remote` matches the codebase's `git remote get-url origin`. Take their
   paths, their *Rules to read* section and the test frameworks their
   checks name.
3. **The investigate skill's private files**, when present: point to them
   under *Production evidence*; never copy their contents.
4. **The ticket itself** (`ticket-source.md`): every Notion page, Figma
   file, Slack link and sibling ticket it reaches, as first entries under
   *Docs* and *Conversations*.
5. **The tracker**: the team's labels and estimate scale, read as
   `/ticket`'s `defaults.md` says, with Linear's `list_issue_labels` or the
   Notion database's schema.
6. **The repo's ticket template**, when the codebase has one.

A project with no codebase anywhere above is the one profile gap that is
a question for Gustavo (SKILL.md § 4): ask for the repo path, once, with
the option to groom from docs alone. Write the profile with what you have
either way, and say in the final message that it was created and where.

## After a run

Update the profile at the end of every groom, by hand (`Edit`), from
`research.md` and `decisions.md`:

- **Learned**: for every answered question, the kind (`flag definition`,
  `collection name`, `prior art ticket`, `customer count`, `design intent`,
  …) and the source that answered it. Merge into an existing line when the
  kind and source match; bump the date.
- **Glossary**: every term the research mapped to a code name, with its
  `path:line`.
- **Dead ends**: every source a researcher searched for a kind of question
  and found empty.
- **Docs, Conversations, Production evidence**: a source that answered and
  was not listed yet.
- Bump `updated:`.

Keep the file under about 150 lines: when *Learned* passes 40 lines, drop
the oldest lines whose kind another line already covers.
