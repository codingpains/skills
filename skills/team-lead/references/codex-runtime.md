# Codex runtime

Read this only when `/team-lead` runs in Codex. It adapts the shared pipeline;
the ticket, worktree, reports, checks, PR flow, review rounds and safety rules
remain unchanged.

## Paths and primitives

- Team Lead skill root: `~/.agents/skills/team-lead/`, not
  `~/.claude/skills/team-lead/`. Substitute this root in every shared
  instruction, handoff and repo profile.
- Specialist playbooks: `~/.codex/agents/team-lead-playbooks/`.
- Use `spawn_agent` for an `Agent` call, `followup_task` for `SendMessage`, and
  `wait_agent` for a foreground wait. A stage is complete only after its final
  report arrives.
- Use an `explorer` agent where the shared instructions say `Explore`. Do not
  override its model; focused exploration is already optimized by the harness.
- Use a `default` agent where they say `general-purpose` (the intake reader,
  the groom's story lookup), without a model override.
- Use available app, plugin or CLI tools by capability. Names such as
  `mcp__claude_ai_Linear__get_issue` describe the required Linear operation,
  not a literal Codex tool name. If a required integration is unavailable,
  stop with the missing capability; do not replace ticket or design data with
  web search.
- Ask the human directly when the shared workflow says `AskUserQuestion`.
  Persist the run state first, end the turn with one concise question, and
  resume from the run directory in the next turn.
- A yielded `exec_command` session replaces a background Bash call. Keep its
  session ID, continue other safe work, and wait with `write_stdin` only when
  the pipeline reaches a step that depends on it.

## Model policy

The Lead uses the model selected for the top-level Codex task; the skill does
not change it. Recommend Terra at medium reasoning for routine runs. Never
select Astra for a specialist automatically.

| Stage | Codex agent | Model | Reasoning |
|---|---|---|---|
| Plan | `team-architect` | `gpt-5.6-sol` | high |
| Implement | `team-coder` | `gpt-5.6-terra` | medium |
| Harden | `team-hardener` | `gpt-5.6-terra` | medium |
| Test | `team-tester` | `gpt-5.6-terra` | medium |
| Review | `team-reviewer` | `gpt-5.6-sol` | high |
| Wrap-up | `team-wrapup` | `gpt-5.6-terra` | medium |
| Assess | `team-assessor` | `gpt-5.6-luna` | medium |

The installed agent configuration owns these choices. Do not pass model or
reasoning overrides to `spawn_agent`. A human may explicitly choose another
model for a run or stage.

## Stage policy

Codex uses the same lean, risk-gated chain as Claude, in
`~/.agents/skills/team-lead/references/stage-gates.md`, so a Plus
subscription does not pay for every specialist on every ticket. `--full`
selects full mode. When usage is the constraint, persist the run and ask the
human whether to wait for the usage reset or continue with an explicitly
chosen smaller chain.

## Agent playbooks

Each Codex TOML agent reads this adapter and its matching Markdown playbook
from `~/.codex/agents/team-lead-playbooks/`. The Markdown frontmatter is Claude
configuration data; follow its body. Apply these substitutions throughout:

- `~/.claude/skills/team-lead/` → `~/.agents/skills/team-lead/`
- `~/.claude/agents/team-*.md` →
  `~/.codex/agents/team-lead-playbooks/team-*.md`
- `~/.claude/agents/references/` → `~/.codex/agents/references/`
- `ToolSearch` → use the callable tool or plugin already exposed to the agent

For other installed skills, use the path from Codex's available-skills catalog
instead of guessing a Claude path.

## Assessment

The Claude transcript parser does not understand Codex rollouts. In Codex, do
not run `scripts/run-metrics.py`. The Assessor reads the run artifacts and the
Codex rollout files under `~/.codex/sessions/` whose timestamps are at or after
`started_at`. Use their last `token_count` event when it can be attributed to
this run. If exact per-stage attribution is unavailable, report total tokens or
allowance deltas as unavailable instead of guessing; still analyze stage time,
send-backs, findings, changed lines and recurring optimization slugs. A metrics
limitation never blocks the PR.
