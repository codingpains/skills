---
name: investigate
description: "Investigate a production problem from a Linear ticket, a Slack thread or a Sentry issue and answer the way Gustavo wants: the root cause, a confidence score on a fixed scale, evidence built on real company / flow / worker IDs, every earlier explanation checked, customer impact, and next steps with an owner. Read-only on production. Reports in chat and never posts to Linear, Slack or GitHub until Gustavo asks, so he can question the findings first. Use when Gustavo says 'launch an investigation', 'investigate', 'dig into', 'research', 'deep dive', 'find the root cause', 'what happened', 'diagnose', or pastes a ticket ID or Slack link about a malfunction. Invoke as /investigate <ticket IDs | Slack links | Sentry issues> [\"my read is …\"]."
argument-hint: "<ticket IDs | Slack links | Sentry issues> [\"my read is …\"]"
---

# /investigate

Gustavo wants four things from every investigation, without having to ask:
**what the problem is, what caused it (with a confidence score), the evidence,
and what has to be done.** He believes a finding when it rests on real
records: a company, a flow, a worker, a timestamp, a count. He expects earlier
explanations (the ticket's, Reef's, a teammate's) to be tested, not repeated.

Arguments: `$ARGUMENTS`.

## Rules

- **Production is read-only.** Never write to a database, a queue, a feature
  flag, a customer setting or a deployment.
- **Nothing leaves this session until he asks.** Don't post, comment, create,
  move, assign or send in Linear, Slack, GitHub or Notion until he says so in
  this session. He questions the report first.
- **Never ask for a token or connection string in chat.** If access is
  missing, name the variable or login he has to set up himself.
- **No runnable code** in anything meant for other people: comments, tickets,
  Slack drafts. Describe steps in prose.
- **Plain language, answer first, short sentences.** Cite `path:line` for code.
- **A claim needs a record.** "It looks like" with no ID, count or timestamp
  behind it is a hypothesis. Label it as one.

## Private files

`$INVESTIGATIONS_HOME`, else `~/.investigations/`, holds what must not go in
this public repo:

| File | What |
|---|---|
| `sources.md` | Where the data lives: database variables per region, naming, Sentry tips, VPN and cluster access. **Read at intake.** |
| `domain.md` | Facts Gustavo has taught: which customers matter most, which code paths are live, team ownership. **Read at intake.** |
| `preflight.conf` | The access checks `scripts/preflight.sh` runs. |
| `index.jsonl` | One line per case, for finding related cases. |
| `<case>/case.md` | The case file: brief, hypotheses, corrections, verdict. |
| `<case>/evidence/` | Raw query and log output. |
| `<case>/report.md` | The last report given in chat. |

If the folder is missing, create it, tell Gustavo, and continue with what you
can reach.

## 0. Open the case

The case name is the first ticket ID in lower case (`onb-1408`), else
`sentry-<short id>`, else `slack-<channel>-<ts>`. Set
`CASE=$INVESTIGATIONS_HOME/<case>` and create `$CASE/evidence/`. If
`case.md` already exists, this is a resume: read it and the report, say
where it stands, and continue from there.

## 1. Intake (ask nothing)

1. **Sort the arguments:** Linear IDs, Slack links, Sentry issues, PRs, and
   free text. Free text is Gustavo's own reading of the problem. It becomes
   hypothesis H1, credited to him.
2. **Read every source in full:** the ticket with all its comments, the Slack
   thread and any thread it links, the Sentry issue, and the PR with its
   review threads. Follow links one level deep.
3. **Several tickets:** read them all before splitting the work. If they
   share a company, a time window, an error or a deploy, investigate them as
   one case and say so.
4. **Past cases:** run
   `bash ~/.claude/skills/investigate/scripts/find-cases.sh <keys>` with every
   key you have: error codes (`#61d172f8`), Sentry short IDs, company and
   flow UUIDs, function names, ticket IDs. Read every matching `case.md`. A
   match can end the case in minutes.
5. **Access:** run `zsh ~/.claude/skills/investigate/scripts/preflight.sh`.
   Whatever is unreachable becomes a blind spot in the framing note, not a
   surprise an hour in.
6. Read `sources.md` and `domain.md`.

## 2. Framing note (post it, don't wait)

Post this within the first few minutes, save it to `case.md`, and keep
working. It lets Gustavo correct a wrong assumption early instead of after an
hour of digging.

```
**Framing — correct me anytime, I'm continuing.**
- Symptom: <one line, as a user would see it>
- Where: <company / flow / worker / task IDs, or "not found yet">
- Code path: <entry point → where it fails>, read at <production branch | main>
- Release: <suspect release and deploy time, or "none in the window">
- Hypotheses:
  H1 <claim> (source: Gustavo | ticket | Reef | <teammate> | me)
  H2 …
- Blind spots: <what preflight could not reach>
```

Every earlier explanation in the ticket, its comments or the thread becomes
its own hypothesis, with its source.

## 3. Gather evidence

Run every check that applies:

1. **One real example.** Find a concrete company, flow, worker and task with
   timestamps that show the symptom. Without one, say the problem is
   unconfirmed.
2. **Timeline.** Line up Sentry's first and last sighting, the deploy times
   of nearby releases (the production branch's release commits), and the
   timestamps in the data. This settles "was it the release?", the question
   behind every release follow-up ticket.
3. **Scale.** Count the affected records by company and by region or stage.
   When the large customers listed in `domain.md` are among them, name them
   with their numbers. That is strong evidence the finding is real. Never
   name a customer the data doesn't show.
4. **The code as it ran.** Read the code at the production branch for what
   happened, and at main for what a fix will change. Cite `path:line`.
5. **Earlier explanations.** Test each one and mark it holds, wrong or
   partly right, with the proof.
6. **Try to break the leading hypothesis.** Ask what you would see if it
   were wrong, then go and look for that.

**Helpers.** When two or more hypotheses need data, or a pull will return
large output (many query rows, a log export), spawn `investigate-probe`
agents in the background. Spawn one per hypothesis or source, all in one
message. Give each one:
- the case folder
- the hypothesis
- what would disprove it
- the IDs and time window
- the access that preflight found

They write raw output to `$CASE/evidence/` and return a verdict with evidence
rows. Do the code reading yourself.

**Keep raw output out of the conversation.** Send any query or log pull
longer than a screen to a file in `$CASE/evidence/`, then read counts,
heads and summaries. Long investigations die from running out of room, not
from hard questions.

**Stop** when the leading hypothesis reaches 80 or more on the scale in
`references/report.md` with every check done, or when the remaining doubt
needs access you don't have. Name that access instead of guessing around it.

## 4. Report

Write the report in chat using `references/report.md`. Save it to
`$CASE/report.md` and update `case.md`. End by listing what you can do next
(post the findings, file the fix tickets, move the ticket), as a plain list.
Do nothing on that list until he picks.

## 5. Questions and corrections

Gustavo will question the report. Answer with records, not reassurance. When
he corrects a fact about the domain:
1. Check what the correction changes, re-run what it affects, and say plainly
   which conclusions moved and which held.
2. Log it under **Corrections** in `case.md`.
3. If it holds beyond this case (which code path is live, what a field means,
   who owns what), add one line to `domain.md`.

## 6. Act, only when asked

- **Comment on the ticket:** use the comment format in
  `references/report.md`. Evidence goes with each claim.
- **Fix tickets, epics, splits, estimates, moves, assignments:** follow
  `~/.claude/skills/ticket/SKILL.md`, and point it at `$CASE` for the
  evidence.
- **Slack:** draft the message for him. Send it only if he says to.
- Re-read whatever you wrote (`get_issue`, the thread) and fix what
  rendered badly.

## 7. Close the case

Update `case.md`: status, root cause, confidence, tickets filed, open
questions. Then write its line to `index.jsonl`, replacing any older line
for the same case (format in `references/report.md`). If you learned a
lasting access trick, add it to `sources.md`. Don't write per-case memory
notes; the case file is the memory.

Read `references/pitfalls.md` before step 3. It lists mistakes Gustavo has
already corrected.
