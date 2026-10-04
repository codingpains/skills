# Confidence scoring

Used by the Lead when it answers `/quill groom` questions before asking the
human, by the Architect, and by any agent that has to answer an open
question about the ticket. Every answer gets exactly one score.

## The scale

| Score | Meaning | Evidence it needs |
|---|---|---|
| **3** | Direct, verifiable evidence | A specific file and line, a doc section, a ticket comment, or a commit that states or shows the answer. Anyone can open it and check. |
| **2** | Strong hints that imply the answer | Existing examples of the same pattern, a sibling feature that does it one way, naming and structure that point one way, with no evidence pointing the other way. |
| **1** | No useful evidence | Nothing in code, docs, history or the ticket settles it, or the evidence conflicts. |

When in doubt between two scores, pick the lower one. A score of 2 needs the
hints written down; "it seems likely" with no citation is a 1.

## Escalation rule

**Score below 2 → escalate to a human, with suggested options.** Only the
Lead talks to the human; agents return escalations in their report and the
Lead asks.

Nobody escalates a 2 or a 3. Decide, and write the evidence down.

## Answer format

One row per question:

```
| # | Question | Answer | Score | Evidence |
|---|---|---|---|---|
| Q1 | Where is the shift end time validated? | `validateShift()` rejects end < start | 3 | `src/shifts/validate.ts:42` |
| Q2 | Should archived locations appear in the picker? | No, filter them out | 2 | Every other picker filters `archived: false`: `src/jobs/JobPicker.tsx:18`, `src/users/UserPicker.tsx:25` |
| Q3 | Should the export include deleted rows? | — | 1 | No spec, no existing export to copy, ticket silent |
```

## Escalation format

Each score-1 item becomes:

```
### Q3. Should the export include deleted rows?
Why it is open: <what was searched, what was missing or conflicting>
Options:
1. <option> (recommended) — <trade-off in one line>
2. <option> — <trade-off>
3. <option> — <trade-off>
```

Two to four options. Recommend one, first, and say why in its trade-off line.
The Lead turns this into an `AskUserQuestion` call with the same options.
