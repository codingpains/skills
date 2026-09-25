# Working in this repo

This repo is the source of truth for my Claude Code skills and agents. The
copies in `~/.claude/skills/` and `~/.claude/agents/` are symlinks back here,
installed by `./install.sh`. Never edit the installed copies; edit here.

- A skill is `skills/<name>/SKILL.md`; its `name:` must equal the folder name.
- An agent is `agents/<name>.md`; its `name:` must equal the file name, and
  `model:` is one of `sonnet`, `opus`, `haiku`, `fable`, `inherit`.
- Skills and agents refer to each other's files by their installed path,
  `~/.claude/skills/<skill>/...`. `scripts/validate.sh` checks those paths
  resolve to files in this repo.

After a change:

1. Run `scripts/validate.sh` and fix what it reports.
2. Commit with a short imperative subject naming the skill or agent
   (`team-lead: resume from any stage`). No co-attribution trailers.
3. If a skill or agent was added, renamed or removed, run `./install.sh`
   and tell me to start a new session.

The `/team-lead` pipeline is split across `skills/team-lead/SKILL.md`, the
six `agents/team-*.md` files, and the shared files in
`skills/team-lead/references/`. A rule every agent follows belongs in
`references/team-rules.md`, not copied into each agent.

Pipeline performance reports live in `~/.team-lead/performance/` (outside
this repo). When asked to improve the pipeline, read `index.jsonl` there
first: optimizations recurring across runs come first.

Repo profiles (`skills/team-lead/repos/<name>.md`) hold per-repo checks.
`/team-lead --configure-repo` writes and commits them here; hand edits are
fine too. Keep `updated:` current when you change a command.

Grooming uses the Quill plugin's `quill:groom`. It is not in this repo; do
not add a grooming skill here. Before adding any skill, check whether an
installed plugin already covers it.
