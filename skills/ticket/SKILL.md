---
name: ticket
description: Create, rewrite, or rearrange tickets the way Gustavo wants them, in any project and any tracker (Linear, a Notion tasks database, GitHub Issues) — evidence-backed, testable acceptance criteria, an estimate, and enough context that a coding agent or any engineer can pick it up cold. Each project's team, labels, estimate scale, test environment and checks come from a project file in ~/.ticket/projects/, built on first use. Use whenever Gustavo says "make/create/open/file a ticket", "ticket this", "write it up in Linear", "make this agent-ready", "these tickets lack context", "rewrite ABC-123", "split this ticket", "move these under the epic", "mark as duplicate", "close it", or after an investigation, QA run, PR review, or Slack thread that ends in tracker work. Invoke as /ticket [create|rewrite|rearrange] [ticket ids or context].
---

# /ticket — tickets, Gustavo's way

A ticket is read **on its own**, by a coding agent or an engineer who saw none of this
conversation. Everything it needs to start work must be in the ticket. A thin ticket is a
failed ticket, even if it is accurate.

Load before writing anything:
- `references/standards.md` — the quality bar and the description templates per ticket type.
- `references/defaults.md` — the defaults every project starts from.
- `references/project-file.md` — how to find, build and update the project file.
- `references/trackers.md` — how to read and write tickets in Linear, Notion or GitHub.
- `references/pitfalls.md` — mistakes already made and corrected. Do not repeat them.

## Pick the mode

| Signal | Mode |
|---|---|
| No ticket exists yet | **Create** |
| An existing ticket ID plus "flesh out", "agent-ready", "lacks context", "rewrite", "update it with…" | **Rewrite** |
| "split", "move under", "parent", "duplicate", "close", "re-link", "follow-up epic" | **Rearrange** |

One request can mix modes (e.g. "split ABC-129 and make the children agent-ready"). Do
rearrange first, then create/rewrite each resulting ticket.

## Step 0 — Find the project

Work out which project the ticket belongs to and load its file from `~/.ticket/projects/`,
as `project-file.md` says. Its values override `defaults.md`. No file yet: build it before
Step 3, say so in the report. Everything below that says "the project's …" (team, labels,
estimate scale, test environment, check command, record IDs, coding agent) comes from it.

## Step 1 — Gather evidence (all modes except pure rearrange)

The ticket comes at the end of an investigation. If the investigation has not happened, do it now.
Do not write from memory or assumption.

- Read the source: the parent/related ticket and its comments, the Slack thread, the PR review
  threads, the QA comment, the pasted email.
- Read the code on the default branch of the project's repo. Verify every file path, function,
  type, table and field name you will cite. A stale specific is worse than a stated unknown.
- Get real evidence: the concrete record IDs the project file names (the account, the record,
  the user it happened to), counts, region, date, environment. Production queries are
  read-only, and the ticket says so.
- If the evidence disproves the problem, **do not file a ticket**. Say so, and correct any earlier
  comment that claimed otherwise.
- Search the tracker for duplicates (`trackers.md` § Search). If one exists, offer to update it
  instead.

## Step 2 — Decide what needs asking

Default: **do not ask, write.** Gustavo rarely wants a draft first.

Ask (plain numbered questions he can answer "1. a 2. yes") only when:
- the answer changes **which** ticket(s) to create, the parent epic, or the scope;
- follow-ups would land under an epic that is about to ship (ask: same epic, or a follow-up epic?);
- the project itself is unclear (no ticket ID, no repo, more than one project fits), or its
  tracker's conventions cannot be read.

Everything else that is unknown goes into the ticket's **Open questions** section, marked
"Must be answered before work starts". Never ask a question you cannot phrase in plain words.

## Step 3 — Write

Use the template for the ticket type from `references/standards.md`, or the repo's own
template when the project file names one. Apply `defaults.md`, then the project file.

**Create:** one create call with all fields (`trackers.md`). Link the source ticket, PR,
design file or Slack thread.

**Rewrite:** fetch the ticket first. Keep what is correct and specific. Replace what is vague.
Keep the existing title unless it is misleading. When Gustavo has answered an open question,
rewrite that part as **settled fact** ("Confirmed: …") and remove "proposed" or "to confirm"
wording everywhere it appears. Batch rewrites (several tickets) each get the full template.
Never shorten them to fit more tickets.

**Rearrange:** see the section below.

## Step 4 — Check after saving (always)

Re-fetch every ticket you touched and check:
- no duplicated headers (e.g. `## Notes## Notes`) and markdown renders cleanly;
- no unwanted auto-links: trackers turn words that look like an issue key, a user or an
  initiative name into mentions. Rephrase or escape them; record any repeat offender in the
  project file;
- labels are not duplicated, and adding a bug label did not attach a response-time deadline
  (SLA) you did not mean. If it did, say so;
- parent, blockers, relations and estimate are as intended.

Fix anything wrong, then report.

## Step 5 — Report and learn

Short: one line per ticket with ID, title, link, estimate, and parent. Name any default you
picked (priority, labels) so he can override it. List open questions that block the work.
Say if the project file was created or changed, and its path.

Update the project file when this run taught something it lacked (`project-file.md`
§ After a run).

## Rearrange

- **Split:** child tickets of 1 to 2 points each (3 max, or the project's equivalent), each
  using the full template, so it stands alone and never says "see parent". Clear the parent's
  estimate. Replace the parent's Fix / What to build with an ordered list of the children. Set
  blocked-by between children where order matters.
- **Move / re-parent:** confirm the target epic when it is about to ship. Follow-ups normally
  go to a separate follow-up epic, with an `[<Epic> follow-up]` title prefix.
- **Duplicate / close:** link the surviving ticket, and leave a one-line comment saying why. If the
  closed ticket had unique evidence, copy it into the survivor first.
- "If actionable create, else close" means: decide per item, with a one-line reason each.
