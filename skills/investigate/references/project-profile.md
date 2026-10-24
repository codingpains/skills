# Project profile

A profile holds what differs between the systems Gustavo investigates: where
the data lives, which IDs a claim rests on, how a deploy shows up, which code
paths are live, and the mistakes already corrected there. The skill stays
general; the profile carries the project.

Profiles live in `$INVESTIGATIONS_HOME/projects/<name>/`, else
`~/.investigations/projects/<name>/`, outside the skills repo, because they
name customers, people and internal systems. `<name>` is the system, not the
team: `wx-system`, `hire`. Several teams' tickets land in one system, and one
team can touch two. Hand edits are welcome; keep `updated:` current.

| File | What |
|---|---|
| `sources.md` | Frontmatter for picking the profile, then where the data lives and how to reach it. |
| `domain.md` | Facts Gustavo has taught: key customers, live code paths, names, ownership, pitfalls only this system has. |
| `preflight.conf` | The access checks `scripts/preflight.sh` runs. |

Cases stay in one place for every project (`<home>/<case>/` and
`index.jsonl`), so a past case is found whatever system it was in.

## Picking the profile

Take the first that applies. Several can apply to one case; load each.
1. A Sentry issue in the arguments: the profile whose `sentry:` lists its
   project.
2. A ticket: the profile whose `teams:` lists its team key. When the key is
   in several profiles, pick by the app, service or repo the ticket and its
   thread name; still unclear, load both.
3. The current directory is in a git repo: the profile whose `repos:` lists
   that remote and folder.
4. Exactly one profile exists: use it, and say so in the framing note.

Nothing fits: build a new profile (below) and say so in the framing note.
Don't ask; the framing note is where Gustavo corrects it.

## sources.md

```
---
name: wx-system
teams: [ONB, CMP]                 # Linear team keys whose tickets usually land here
sentry: [fountain/wx-system]      # Sentry org/project slugs
repos:                            # remote + folder, then the local checkout
  - github.com/acme/monorepo apps/wx-system  /Users/me/src/monorepo
updated: 2026-10-23
---

## Records
<the IDs a finding rests on (for example account / order / user), the
tenant key every query should filter on first, and the stage or region
names counts are split by.>

## Data
<each read-only store: the env var that holds its connection, the stage it
covers, naming, how to query it fast, and what is withheld (PII views).>

## Errors and logs
<Sentry projects and how to query a time range; what is sampled; when
collection started.>

## Code and releases
<the main checkout; what ran in production (a branch, a tag, a deploy log)
and how deploys are named and timed; how an error code maps to a line.>

## Access gaps
<what can't be reached and who could check it.>
```

## domain.md

Plain sections, one short dated line per fact: **Customers** (the ones that
matter most; name them when the data shows them), **Live code paths**
(flags, old and new paths, which one most traffic takes), **Names** (the
exact store or field the code uses for a loose word), **Ownership**,
**Pitfalls** (mistakes only this system invites). Never name a customer the
data doesn't show.

## preflight.conf

One check per line, `kind|label|target`; `scripts/preflight.sh` lists the
kinds. A store with no kind of its own uses `cmd` with a read-only command.

## Building one

When nothing matches, build the profile from what the machine already
knows, before evidence gathering. Each source is optional:
1. `/ticket`'s project file (`~/.ticket/projects/<KEY>.md`) and `/groom`'s
   profile (`~/.groom/projects/<KEY>.md`) for the ticket's team: repos,
   evidence IDs, domain notes.
2. Team-lead repo profiles (`~/.team-lead/repos/*.md`) whose remote
   matches: the checkout and the default branch.
3. The repo: the database clients it uses, the names of the env vars that
   hold their connections (never their values), the deploy workflow, the
   Sentry project in its config.
4. `~/.zshrc`: which of those env vars are set (names only).

Write what is known and mark the rest unknown. Unknown access is a blind
spot, not a guess.

## After a run

A domain correction that holds beyond the case goes to `domain.md`; a
lasting access trick goes to `sources.md`. Correct a wrong line rather than
add a second one, and bump `updated:`.
