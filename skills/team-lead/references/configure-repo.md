# Configure a repo

Read by the Lead when `/team-lead` is called with `--configure-repo [path]`.

With `--configure-repo [path]` there is no ticket and no pipeline. Build or
refresh the validation profile for the repo the session is in, following
`repo-profiles.md`.

1. **Which repo and area.** Normalize the remote as in `repo-profiles.md`
   § Matching. The area is the `path` argument, relative to the repo root;
   without one, use the whole repo, or ask when the repo is a monorepo with
   several apps. Name the profile `<repo>-<area-folder>` (`megalith-wx-system`)
   or `<repo>` for a whole repo. If a profile with that name exists, this is
   a refresh: read it first and keep what still holds.
2. **Research.** `git fetch origin <default>` and read from
   `origin/<default>`, never the working tree. Cover the sources in
   `repo-profiles.md` § Creating, in order. For a large area, spawn
   `Explore` agents in parallel (for example: CI and hooks; docs and rules;
   package scripts and tool configs), each told to read from
   `origin/<default>` and return exact commands with the file they came
   from.
3. **Draft** the profile in the format of `repo-profiles.md`. Every command
   must exist: the script is defined, the binary is a dependency, the flag
   is accepted by that tool's version. Mark anything you could not confirm
   with `(unverified)`. Prefer file-scoped commands; say which checks can
   only run per workspace.
4. **Show it** to the human, and for a refresh the diff against the old one.
   Ask with `AskUserQuestion`: save it, or make changes (fold them in and
   show it again).
5. **Save and commit.** Find the skills repo behind the symlink:
   `SKILLS_REPO=$(cd "$(dirname "$(readlink ~/.claude/skills/team-lead)")/.." && pwd)`.
   If `~/.claude/skills/team-lead` is not a symlink (a copy install), stop
   and give the human the profile to add by hand. Otherwise write
   `$SKILLS_REPO/skills/team-lead/repos/<name>.md`, run
   `$SKILLS_REPO/scripts/validate.sh`, and commit only that file:
   `git -C "$SKILLS_REPO" commit -m "team-lead: add|refresh <name> repo profile" -- skills/team-lead/repos/<name>.md`.
   Approval in step 4 covers this commit.

End with the profile path, the commit, and anything marked `(unverified)`.

