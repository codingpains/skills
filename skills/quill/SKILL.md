---
name: quill
description: Quill, a software design assistant that writes user stories to Notion and aligned designs to Figma. Run as /quill <command> [args], with command one of setup, switch-project, new-feature, change-request, groom, catalogue-from-code or polish-ui. Use when the user wants to set up a Quill project, design a new feature, process a change request, groom a Linear or Notion ticket, catalogue stories from existing code, or polish a Figma design layer.
argument-hint: "<setup|switch-project|new-feature|change-request|groom|catalogue-from-code|polish-ui> [args]"
---

# Quill

The first word of the arguments names the command; the rest are that
command's arguments.

| Command               | File                                                    |
| --------------------- | ------------------------------------------------------- |
| `setup`               | `~/.claude/skills/quill/commands/setup.md`               |
| `switch-project`      | `~/.claude/skills/quill/commands/switch-project.md`      |
| `new-feature`         | `~/.claude/skills/quill/commands/new-feature.md`         |
| `change-request`      | `~/.claude/skills/quill/commands/change-request.md`      |
| `groom`               | `~/.claude/skills/quill/commands/groom.md`               |
| `catalogue-from-code` | `~/.claude/skills/quill/commands/catalogue-from-code.md` |
| `polish-ui`           | `~/.claude/skills/quill/commands/polish-ui.md`           |

With no command or an unknown one, list the commands with a line each from
the overview and ask which to run.

Before running a command:

1. Read `~/.claude/skills/quill/references/overview.md`. Its rules and its
   `AskUserQuestion` guidance apply to every command.
2. Read the command's file and follow it. Its arguments, such as a ticket ID
   for `groom`, are the words after the command name.

## Where Quill keeps its state

Quill home is `$QUILL_HOME`, else `~/.quill/`. Every `quill.config.json` and
`projects/<slug>.notes.md` the commands and agents read or write is in Quill
home, never in this skill's folder: the skill is a symlink into the skills
repo, and user state does not belong there. Create Quill home when `setup`
first writes to it.

## Agents

The agent prompts in `~/.claude/skills/quill/agents/` are not registered
subagent types. Dispatch one with the Agent tool (general-purpose) at the
`model` the command names, and pass the agent file's contents as the prompt
together with the inputs the command lists.
