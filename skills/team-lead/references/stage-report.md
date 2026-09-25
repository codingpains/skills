# Stage report

Every agent ends with exactly this report, and nothing after it. Sections
that do not apply say `none`; never drop a section.

```
## <Stage> report — <TICKET_ID>

Status: DONE | DONE_WITH_CONCERNS | BLOCKED
Summary: <two or three plain sentences: what you did and why>

### Commits
<short-sha> <subject>
(or: none — read-only stage / nothing to change, and why)

### Files changed
<path> — <one-line reason>

### Acceptance criteria
| AC | Status | Evidence |
|---|---|---|
| AC1 | met / not met / not affected by this stage | <file:line, test name, or command output> |

### Validations
| Command | Scope | Result |
|---|---|---|
| `npm run lint -- src/foo.ts` | touched files | pass |
| `npx vitest run src/foo.test.ts` | touched tests | pass (12 tests) |

Not run: <command — reason>, or none
Pre-existing failures: <command — evidence it fails on the base commit>, or none

### Stage-specific
<what your agent file asks for here: plan ID, measurements, coverage table,
edge cases, findings, applied fixes>

### Concerns
<things outside your scope or remit the Lead should know>, or none

### Escalations
<score-1 items in the format of confidence-scoring.md>, or none
```

`BLOCKED` means you could not finish and the Lead must act: say exactly what
stopped you and what you tried. `DONE_WITH_CONCERNS` means the work is
complete and the concerns need the Lead's eye.
