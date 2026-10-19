# PR watch

Read by the Lead when `/team-lead` is called with `--watch <PR>`. Section
numbers without a file name (§ 10, preflight step 5) are in `SKILL.md`;
R-numbers are in `review-rounds.md`.

`--watch <PR> [--dry-run]` babysits an open PR of this ticket until it
merges. It waits for the repo's bot and CI gates to finish on the PR's
latest commit, then starts a review round with what failed, without waiting
for a person's review. Once the bots say the PR is fit for a person to look
at, it asks for a review in Slack. It turns on auto-merge once everything
passes, and removes the worktree after the merge. It never writes code
itself: rounds run in their own session.

**Run it in a session of its own.** Each wake-up re-reads the session, so a
watcher in the session that built the PR pays for that whole history on
every wake. Started fresh, a wake-up costs a few thousand tokens.

With `--dry-run` it does everything up to starting a round, asking for a
review or turning on auto-merge, writes the context, says what it would
have done, and stops.

## Start a watcher

Called from § 10, T9 and R7, once the PR is pushed. Skip it when `run.json`
`watch.status` is `watching`: a watcher already runs. Skip it for a draft
PR too, and say in the final message to start it once the PR is ready.

With a `t3_thread_launch` tool, launch a thread titled
`<TICKET_ID> watch`, with `workspaceStrategy: {"type": "root"}` (the
watcher works from the main checkout, never from the worktree it may
remove) and the message `/team-lead <TICKET_ID> --watch <PR URL>`. Save its
thread ID as `watch.thread` in `run.json`. Otherwise give the human that
line to paste into a new session. A watcher that died is restarted the same
way: it resumes from `run.json`.

## The tools

All under `~/.claude/skills/team-lead/scripts/`. They read GitHub and never
write to it.

- `pr-gates.py <PR URL>` scores the PR against the repo's gates file
  (`repo-profiles.md` § PR gates). `--summary` prints one line per gate.
- `pr-watch.sh <PR URL> <watch dir>` re-scores every 5 minutes into
  `<watch dir>/state.json`. It exits when the state is news, or after
  6900 s. `pr-watch.sh --ack <watch dir>` marks the current state as acted
  on, so the next run waits for something new. It also exits, even while a
  gate runs, when `review_ready` is true and `<watch dir>/review-asked` does
  not exist.
- `pr-context.py <state.json> --out <file> --skip-keys <file>` writes what
  failed: Reef findings, QA cases with expected and actual, people's threads
  and comments, and failed CI with its `rwx results` summary.

## W1. Load

1. Run preflight steps 1 and 2 (main checkout, `gh`).
2. Find the run directory as in R1 step 2. Without one, stop: the watcher
   needs the ticket and the worktree a run records.
3. The watch dir is `<run dir>/watch/`. In `run.json`, create or keep a
   `watch` object:
   `{"pr", "started_at", "status": "watching", "auto_rounds": 0, "triggers": [], "requests": [], "merge_enabled": null}`.
   A watcher that restarts keeps the object and the watch dir, so it
   never acts twice on the same state.
4. Read the gates file's `max_auto_rounds` (3 when absent) and `merge`
   (`gh pr merge {pr} --auto --squash` when absent).
5. Write the start of the watch to `notes.md`.

## W2. Arm

Run `bash ~/.claude/skills/team-lead/scripts/pr-watch.sh <PR URL> <watch dir>`
with `run_in_background: true` and `timeout: 7200000`. End your turn. Never
poll it, and never `sleep`: its notice wakes you (team-rules § Working
habits). Read only the last lines of its output: the gate summary and the
`watch:` line.

## W3. Act

Act on the `watch:` line and on `overall` in `<watch dir>/state.json`.
First, when `review_ready` is true and `<watch dir>/review-asked` does not
exist, do W8. Then the row below. After every action,
`pr-watch.sh --ack <watch dir>`, a line in `notes.md`, and back to W2,
unless the row says stop.

| Line or `overall` | Do |
|---|---|
| `watch: timeout` | back to W2 |
| `running` | nothing more: the watcher woke for W8 only |
| `watch: error` | back to W2 once; a second error in a row: tell the human the error and stop |
| `stalled` | W4 |
| `round-needed` | W5 |
| `conflict` | W5, with the note `merge <base>: the branch conflicts with it` |
| `ready` | W6 |
| `merged` | W7, then stop |
| `closed` | tell the human, set `watch.status` to `stopped`, and stop; leave the worktree |

## W4. A gate waits

`waiting_on` names the gates that nothing is working on.

- A gate with a `request` in the gates file, when this head has no entry
  in `watch.requests` and the gate's `summary` does not say a run is going:
  post the request on the PR (`gh pr comment <PR> --body '<request>'`) and
  add `{"gate", "head", "at"}` to `watch.requests`. Post it only once per
  head: a second request cancels the run the first one started.
- `human`: tell the human once per head, in one line: who is asked to
  review (`gh pr view <PR> --json reviewRequests`), each other gate's
  summary, and whether W8 asked for a review in Slack. Failed bot or CI
  gates never wait for a person: they start a round (W5).
- Any other gate: tell the human its summary once per head.

Your message is the notice. Post nothing else on the PR, and nothing in
Slack beyond W8.

## W5. Start a round

1. **Nothing new.** When the state has items and every item key is already
   in an earlier trigger, a round has had them all (a round that only replied pushes nothing):
   go back to W2.
2. **Limit.** Stop and ask the human when `watch.auto_rounds` has reached
   `max_auto_rounds`, or when an item's key without its `@<commit>` suffix
   (`qa:CT4`, `reef:F7`, `ci:RWX: CI`) is in two earlier triggers: the
   rounds are not converging. Give the context file from step 3 and the
   round line from step 4 so the human can start it by hand.
3. **Context.** Write every item key of earlier triggers to
   `<watch dir>/handled`, then run
   `pr-context.py <watch dir>/state.json --out <watch dir>/context-<head7>.md --skip-keys <watch dir>/handled`.
   For a conflict, add the note at the top of the file.
4. **Round line.** `/team-lead <TICKET_ID> --round <PR URL> --auto --context <context file>`.
5. **Start it.** With `--dry-run`, print the line and the context file's
   path, and stop. With a `t3_thread_launch` tool, launch a thread titled
   `<TICKET_ID> round <n>`, with
   `workspaceStrategy: {"type": "existing_worktree", "worktreePath": <run.json worktree>, "branch": <head branch>}`
   and the round line as `message`. Otherwise give the human the line to
   paste into a new session.
6. Add `{"at", "head", "keys", "context", "thread"}` to `watch.triggers`
   and add 1 to `watch.auto_rounds`.

While the round runs, the PR's state stays the same, so the watcher sleeps
until the round's push moves the head. A round that pushes nothing leaves
the state as it is. The watcher wakes when a gate or a person adds
something new.

## W6. Ready

- A draft PR: tell the human it is ready to mark ready for review. Never
  mark it yourself.
- `auto_merge` already on: nothing to do.
- `watch.merge_enabled` is set but `auto_merge` is off: something turned it
  off (a merge-queue failure, a person). Tell the human, and do not turn it
  on again.
- Otherwise run the gates file's `merge` command with `{pr}` set to the PR
  number, from the main checkout. Record its time in
  `watch.merge_enabled`. With `--dry-run`, print the command instead.

## W7. Merged

1. Set `watch.status` to `merged`.
2. Clean up the worktree from `run.json`, only when
   `git -C <worktree> status --porcelain` prints nothing and
   `git -C <worktree> rev-parse HEAD` is the PR's merged head (`head` in
   `state.json`):
   `git worktree unlock <worktree> && git worktree remove <worktree>`.
   Otherwise leave it and say why.
3. **Final message:** the PR and when it merged, the rounds the watcher
   started (one line each: head, items, thread), the requests it posted,
   and whether the worktree was removed.

## W8. Ask for a review

`review_ready` in `state.json` means no person has approved yet, and the
gates in the gates file's `ask_review_after` (every gate but the human one
when absent) are far enough along: Reef says low risk or approved this
commit, QA has no failed case and at most `max_blocked` blocked ones, and
any other listed gate passes. CI may still be running. Ask once per PR,
not per commit.

1. **Skip** when `run.json` has `slack` (a post already went out, as
   takeover.md T8 does) or `slack_skip` (`--no-slack`, or the profile says
   `Slack: none`). Write the reason to `<watch dir>/review-asked` and go on
   with W3.
2. **Message.** `slack-message.md` from the run directory when § 10 wrote
   it; otherwise build it as § 10 *Notify* does. Add a last line with the
   Reef and QA gate summaries from `state.json`, e.g.
   `Reef: no_blockers, risk low · QA: 12 pass, 1 blocked`.
3. **Post.** With `--dry-run`, print the message and the channel, and
   stop. Otherwise load `mcp__claude_ai_Slack__slack_send_message` with
   `ToolSearch` and post it to `run.json` `slack_channel` (§ 10's default
   channel when absent). Save the post's link as `slack` in `run.json`, and
   write it to `<watch dir>/review-asked`.
4. **No tool, or the post failed.** Tell the human, with the message and
   the channel in a code block to paste. Write the reason to
   `<watch dir>/review-asked` all the same, so the watcher asks only once.
