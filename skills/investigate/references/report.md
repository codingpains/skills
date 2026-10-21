# Report formats

## Confidence scale

Give one number for the root cause. When the trigger and the full chain have
different certainty, give one number for each ("90% the flow edits
triggered it; 75% the timeouts kept it going").

| Score | What it takes |
|---|---|
| 95–99 | Reproduced, or production logs show the exact sequence with timestamps for a real case. |
| 80–90 | Production data matches on every point and the code shows how it happens, but no live case was caught in the act. |
| 60–75 | The data fits, but at least one link in the chain is inferred. |
| 30–55 | A plausible hypothesis that some data supports. |
| under 30 | A guess. Say what would test it. |

Always say what keeps the score from 100 and what would raise it.

## Chat report

```
## <ticket>: <root cause in one line>

**Confidence: <n>%.** <one sentence on why, and what keeps it from 100>
<Was it the release? One line, yes or no, with the deploy time.>

## Your focus: <the focus note>
<Only when he gave one. The direct answer to it, with its records. Say if
the root cause lies outside it.>

## What happened
<3–6 numbered steps, from trigger to symptom, each with path:line or a record>

## Evidence
| Check | Result |
|---|---|
| Real example | company / flow / worker IDs, timestamps |
| Timeline | first seen, deploys, data timestamps |
| Scale | counts by company and region; large customers named with numbers |
| Code | path:line |

## Earlier explanations
- <source>: <claim>. **Holds / Wrong / Partly**: <the proof>.

## Customer impact
<One plain paragraph a support engineer could forward: what customers saw,
who, since when, and whether it still happens.>

## Not checked
- <what you couldn't reach or didn't test, and what it would change>

## What to do
1. <action>: owner <team or person>, <agent-ready (Reef can do it) | needs a person>, <rough size>
2. …
<Data repair needed? Who runs it?>

**I can do next:** post these findings on <ticket> · file the fix tickets with /ticket · <other>.
```

Keep it scannable. Use tables for evidence and bullets for everything else.
No paragraph longer than four lines, except the customer impact one.

## Linear comment (only when asked)

Same sections as the chat report, without the "I can do next" line. Every
claim carries its proof: the Sentry link, the record IDs, the counts, the
`path:line`. Mark anything not yet done as "not done yet". No runnable code
and no connection details.

## case.md

```
# <case>: <title>
Status: open | reported | acted | closed — <date>
Sources: <tickets, threads, Sentry issues, PRs>
Keys: <error codes, Sentry IDs, company/flow UUIDs, functions> (for find-cases)

## Framing
<the framing note>

## Hypotheses
- H1 (<source>): <claim> — <supported | disproved | open>, <proof or evidence file>

## Corrections
- <date>: Gustavo: <what he corrected> → <what changed>

## Verdict
<root cause, confidence, what to do; tickets filed>
```

## index.jsonl line

One JSON object per line, one line per case:

```
{"case":"onb-1408","date":"2026-10-14","status":"reported","title":"…","root_cause":"…","confidence":90,"area":"service-todo notifications","keys":["#61d172f8","WX-SYSTEM-47G","demoLoad.controller.ts"],"tickets":["ONB-1408"]}
```
