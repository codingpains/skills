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

| Stage | T3 role | Pinned model and reasoning |
|---|---|---|
| `reviewer` | `review` | `~/.codex/agents/team-reviewer.toml` |

Only read-only stages are here. A stage that commits raises commit and
attribution questions this file does not answer yet. Any other name: stop
before any work, name the stages this table supports, and ask the human to
call again.

## Preflight check

Run it at preflight step 2 (and § Review rounds R1), so a missing Codex
surfaces before any work, not at the stage. In order, stopping at the first
failure:

1. **T3 tools reachable.** Load `orchestrator_capabilities`, `delegate_task`
   and `task_status` with `ToolSearch`. Their names may carry a prefix such
   as `mcp__t3-code__`. Not found means the session is not inside T3.
2. **The pin.** For each stage, read `model` and `model_reasoning_effort`
   from its file in the table above.
3. **The catalog.** Call `orchestrator_capabilities`. The provider with
   `providerInstanceId` `codex` must have `canRunCrossProviderChildTask:
   true` and empty `constraints`; the pinned model ID must be in its
   `models`; the pinned reasoning value must be one of that model's
   `reasoningEffort` options.

Never choose a model by name or version: only the pinned ID is used. To
change a stage's model, edit its pin file.

Any failure: one `AskUserQuestion` naming the failed check, with the options
"Run on Claude (recommended)" and "Stop". Record the answer in `notes.md`.

## What to record

A `cross_provider` object in `run.json` (in a round, in that round's entry):

```
{"stages": ["reviewer"], "provider": "codex",
 "models": {"reviewer": {"model": "gpt-5.6-sol", "reasoning": "high"}},
 "checked_at": "<date -u +%FT%TZ>", "fallback": null,
 "tasks": [{"stage": "reviewer", "taskId": "...", "childThreadId": "...",
            "clientRequestId": "...", "started_at": "...", "ended_at": "...",
            "status": "..."}]}
```

`fallback` is `null`, or the reason the stage ran on Claude instead. One
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

- `target`: `providerInstanceId` `codex`, the pinned `model`, and
  `options` `{"reasoningEffort": "<pinned value>"}`;
- `role`: the stage's T3 role from the table;
- `runtimeMode` `full-access`: Codex's workspace sandbox blocks writing the
  report to `~/.team-lead/runs/` and the network for `npx planbin get`. The
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

A failed task, a provider error or a refused model: run the stage's Claude
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
