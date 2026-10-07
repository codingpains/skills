# Stage gates

The Lead picks which specialist stages a ticket runs. By default the chain is
**lean**: the Architect, Hardener and Tester run when the ticket's size or
risk calls for them, not on every ticket. `--full` selects **full** mode,
which runs every stage. Record `mode` and the selected `chain` in `run.json`,
and update `chain` each time a gate adds or skips a stage.

## Initial chain

- Estimate 0 or 1: Coder, Reviewer.
- Estimate 2 or 3: Architect, Coder, Reviewer.
- Estimate 5 or more, or any full-risk trigger below: full chain — Architect,
  Coder, Hardener, Tester, Reviewer, Wrap-up when review produces fixes.
- No estimate: Architect, then decide from its *Risk triggers* line and the
  plan's *Risks* section. Do not select full merely because the estimate is
  absent.

Full-risk triggers are schema or data migration, authentication or
authorization, secrets, payments, concurrency, cross-service contracts,
public API compatibility, destructive operations, a security-sensitive path,
or a plan spanning both backend and frontend. The human's `--full` always
wins.

## Gates after implementation

Decide after the last Coder report, from that report's *Gate signals* and
`git diff --shortstat <base>..HEAD`.

Add the Hardener when any of these holds:

- full mode;
- the Coder changed more than 8 production files or 400 non-generated lines;
- the Coder reports a plan deviation, rule exception, complexity warning,
  duplicated logic, or maintainability concern;
- the plan includes a refactor or one of the full-risk triggers.

Add the Tester when any of these holds:

- full mode;
- the change fixes a bug that needs regression proof;
- it changes stored data, a public contract, permissions, asynchronous or
  concurrent behavior, or designed UI states;
- the Coder reports missing edge-case coverage, a pre-existing failure that
  obscures the change, or coverage below a repo-profile target.

The Reviewer always runs. The Wrap-up runs only when the review fix list is
non-empty. The Assessor runs once after PR publication, never between
stages.

## A skipped stage

Write one line in `notes.md` for each gate: the stage, added or skipped, and
the condition that decided it. In the handoff of the next stage, say under
*Your task* which stages the gates skipped and why: `Gates: Hardener
skipped (5 production files, 180 lines, no Coder signals); Tester ran
(changes permissions)`. The Reviewer takes on a lighter form of a skipped
stage's checks (`team-reviewer.md`).

Do not add a stage merely because budget remains, and do not skip a
triggered stage to save it. When budget is the constraint, persist the run
and ask the human whether to wait or continue with an explicitly chosen
smaller chain.
