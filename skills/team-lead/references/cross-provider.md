# Cross-provider stages

Read this only when the call carries `--cross-provider <stages>`. The named
stages run on Codex, through T3's cross-provider handoff, instead of on
Claude. The Lead and every other stage stay on Claude. The ticket, worktree,
handoff, report checks and PR flow do not change.

## When it applies

- The Lead runs in Claude Code. When it runs in Codex, every stage already
  runs on GPT: say so in one line and ignore the flag.
- Only this call. A `--from` or `--round` call without the flag runs every
  stage on Claude, even when the run started with it: the run may resume on a
  computer with no Codex account.
- The value is a comma-separated list of stage names, as `--from` spells
  them (`reviewer`, `wrapup`, ...). It is required, so the word after the
  flag is never a round's note.

## Supported stages

| Stage | T3 role | Pinned model and reasoning | Accepted substitutes, in order |
|---|---|---|---|
| `reviewer` | `review` | `~/.codex/agents/team-reviewer.toml` | `gpt-6-sol`, `gpt-6.1-sol`, `gpt-5.6-sol` |

Only read-only stages are here. A stage that commits raises commit and
attribution questions this file does not answer yet. Any other name: stop
before any work, name the stages this table supports, and ask the human to
call again.

## Preflight check

Run it at preflight step 2 (and `review-rounds.md` § R1), so a missing Codex
surfaces before any work, not at the stage. In order, stopping at the first
failure:

1. **T3 tools reachable.** Load `orchestrator_capabilities`, `delegate_task`
   and `task_status` with `ToolSearch`. Their names may carry a prefix such
   as `mcp__t3-code__`. Not found means the session is not inside T3.
2. **The pin.** For each stage, read `model` and `model_reasoning_effort`
   from its file in the table above.
3. **The catalog.** Call `orchestrator_capabilities`. The provider with
   `providerInstanceId` `codex` must have `canRunCrossProviderChildTask:
   true` and empty `constraints`.
4. **The model.** Use the pinned model ID when it is in the provider's
   `models`. When it is not, use the first of the stage's accepted
   substitutes that is, without asking: models are retired, and a missing
   pin must never stop a run. Use the pinned reasoning value when the chosen
   model offers it in `reasoningEffort`, else the nearest offered value
   below it. Write the substitution in one line of `notes.md` and say it in
   the final message, so the pin file gets updated.

Never choose a model outside the pin and its substitutes list. To change a
stage's model, edit its pin file and the list above.

A failure of checks 1–3, or no accepted model in the catalog: one
`AskUserQuestion` naming the failed check, with the options "Run on Claude
(recommended)" and "Stop". When the session cannot ask (non-interactive),
take "Run on Claude" and set `fallback` to the failed check. Record the
outcome in `notes.md`.

## What to record

A `cross_provider` object in `run.json` (in a round, in that round's entry):

```
{"stages": ["reviewer"], "provider": "codex",
 "models": {"reviewer": {"model": "gpt-6-sol", "reasoning": "high",
                         "substituted_for": null}},
 "checked_at": "<date -u +%FT%TZ>", "fallback": null,
 "tasks": [{"stage": "reviewer", "taskId": "...", "childThreadId": "...",
            "clientRequestId": "...", "started_at": "...", "ended_at": "...",
            "status": "..."}]}
```

`fallback` is `null`, or the reason the stage ran on Claude instead.
`substituted_for` is `null`, or the pinned model the catalog lacked. One
`tasks` entry per delegation, send-backs included.

## The handoff

The task text is the stage's normal packet (`handoff.md` § Each stage's
prompt), preceded by a short header in prose: you are the `<Stage>` stage of
`/team-lead`, running in Codex through T3; read
`~/.agents/skills/team-lead/references/codex-runtime.md`, then
`~/.codex/agents/team-lead-playbooks/team-<stage>.md`, in full, and follow
the playbook with that file's substitutions; you have full access, but stay
read-only exactly as the playbook says; write your report to the report file
and return only the part `stage-report.md` names.

Call `delegate_task` with:

- `target`: `providerInstanceId` `codex`, the `model` the preflight chose,
  and `options` `{"reasoningEffort": "<the reasoning it chose>"}`;
- `role`: the stage's T3 role from the table;
- `runtimeMode` `full-access`: Codex's workspace sandbox blocks writing the
  report to `~/.team-lead/runs/`, outside the worktree. The
  playbook keeps the stage read-only, and `check-stage.sh` proves it;
- `interactionMode` `default`, `mode` `wait`, `timeoutMs` `2400000`
  (40 minutes);
- `title` `<Stage> — <TICKET_ID>`;
- `clientRequestId` `<TICKET_ID>-<stage>`, or `<TICKET_ID>-r<n>-<stage>` in
  a round, with `-2`, `-3` for each send-back. Reuse the same ID when
  retrying the same call, so T3 does not start it twice.

## Waiting

When the call returns `waitTimedOut`, write the run state, tell the human in
one line that the stage is still running on Codex, and end the turn. T3 wakes
the thread when the child finishes. Never poll and never start a watcher. On
waking, read the result once with `task_status`.

## The result

Set the task's `ended_at` and `status` in `run.json`. The task's `summary`
is the returned part. A missing report file: write the
summary there yourself, as SKILL.md § 4–7 says for any stage. Then run
`check-stage.sh` as for any stage: its clean-tree and commit checks are what
prove a read-only stage stayed read-only.

## Failure

A refused model: retry once with the next accepted substitute in the
catalog, as a new `clientRequestId` with `-m2`. A failed task, a provider
error, or no substitute left: run the stage's Claude
agent through `Agent` with the same packet, set `fallback` to the reason,
and write one line in `notes.md`. Do not ask: the run is nearly done, and the
stage on Claude is always acceptable. The final message says so.

## Send-back

A new `delegate_task` whose task text carries the original packet, the
failed check and the previous summary. Never `SendMessage`, and never
`t3_thread_send` to the `childThreadId`.

## Design

The Codex child has no Figma tools. The stage judges from the images in
`<run dir>/design/` and the captures (`team-reviewer.md` § 2 step 8).

## Usage

A Codex stage counts against the ChatGPT plan, not Claude.
`run-metrics.py` cannot see it; the Assessor reads `cross_provider.tasks`.
