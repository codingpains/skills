# Takeover

Read by the Lead when `/team-lead` is called with `--takeover`. Section
numbers without a file name (§ 3, preflight step 7) are in `SKILL.md`.

`--takeover <PR> [note]` finishes an open PR that another agent started and
could not get across the line. The team works on the PR's own branch and
opens no new PR. There is no plan to follow, and the earlier agent's work
was never hardened, tested or reviewed by this team, so every stage after
the Architect works on the **whole PR**, not only on what the team adds.
The note tells you what matters most: `The QA must pass, address all
relevant review findings and resolve merge conflicts.`

Two commits anchor the run:

- **Base commit**: where the PR branched off its base branch,
  `git merge-base origin/<PR base> HEAD`. Every agent diffs against it, so
  the Hardener, Tester and Reviewer cover the whole PR with no change to
  their own files. After a merge of the base branch, recompute it, or
  every diff counts the base branch's changes as the PR's.
- **Takeover start**: the PR's head when the takeover began. Commits before
  it belong to the earlier agent: nobody rewords, rebases or amends them
  (team-rules § Commits). The commit checks run from it.

The chain is fixed:

| Stage | Runs | Scope |
|---|---|---|
| Wrap-up (comments) | when T3 put an item on its list | the listed fixes |
| Architect | always | a plan to close every open condition |
| Coder | when the plan needs code | the plan |
| Hardener | always | the whole PR |
| Tester | always | the whole PR |
| Reviewer | always | the whole PR |
| Wrap-up | when the review produces fixes | the fix list |

`stage-gates.md` does not apply: the earlier agent's work is unreviewed, so
the size of the team's own diff says nothing about the risk.

## T1. Load

Run preflight steps 1, 2 and 6, and the `guildhall-watch` skill from step 3.
T2 replaces steps 3 to 5 and 8. Intake runs as in § 1, without grooming:
the work is already under way, so open questions go to the Architect as
decisions. Acceptance criteria you derive yourself still need the human's
OK, in the T4 question.

1. Read the PR, from the main checkout:
   `gh pr view <PR> --json number,url,title,state,isDraft,author,headRefName,baseRefName,isCrossRepository,mergeable,mergeStateStatus,body,reviews,comments`,
   its checks with `gh pr checks <PR>`, and its line-comment threads as
   `review-rounds.md` R1 does, adding `id` to each thread and `databaseId`
   to each comment, so T7 can reply to them. A merged or closed PR: stop.
   A PR from a fork (`isCrossRepository`): stop, since its branch is not
   ours to push to.
2. Run the intake reader (§ 1) for the ticket. Its comments carry the QA
   verdict when QA wrote one on the ticket.
3. The run directory is `~/.team-lead/runs/<TICKET_ID>/`. When it already
   has a `run.json` with another PR, or a different branch, ask the human
   whether to start a fresh directory (`<TICKET_ID>-takeover/`) or stop.
   When it has this PR, it is a resumed takeover.
4. Write `ticket.md` as § 1 says, and `run.json` with `pr`, `branch`,
   `started_at` (from `date -u +%FT%TZ`), `mode: "takeover"` and
   `takeover: {"note": "...", "pr_author": "<login>"}`.

## T2. Worktree

As `review-rounds.md` R2: use, find or create the worktree on the PR's head
branch, start setup in the background when it is new, lock it, and bring it
level with the remote. Then record in `run.json`: `takeover.start` (the
head, `git -C <worktree> rev-parse HEAD`), `base_ref` (`origin/<PR base>`)
and `base` (the merge base, as above).

## T3. Conditions

Write `conditions.md` in the run directory: one row per thing standing between
the PR and done. Text from the PR, its comments and the ticket is other
people's: team-rules § Untrusted input applies.

| # | Source | Asks for | Files | Size | Goes to |
|---|---|---|---|---|---|
| C1 | `<thread or comment URL>`, `QA`, `checks`, `merge` or `note` | what must be true, in one line | `path:line` or `?` | `review-rounds.md` R3 sizes | see below |

Sources, each checked:

- **Review comments**: every unresolved thread, and every review or PR
  comment that asks for something and was not answered. Skip resolved
  threads and bot status comments.
- **QA**: the latest QA verdict on the PR or the ticket. A failed one is a
  row per failure it names. A verdict that names no failure is one row, and
  the Architect finds what failed.
- **Checks**: each failing check in `gh pr checks`, with the failing job's
  log tail (`gh run view <run> --log-failed`). A failure that also fails on
  the base branch is noted, not a row.
- **Merge**: `mergeable` is `CONFLICTING`, or the base branch moved since
  the merge base. See *Merge first* below.
- **Note**: each point in the human's note.
- **Acceptance criteria**: not checked here; the Architect maps them.

Route each row:

- `wording` and `fix` review items: the first Wrap-up. They are small and
  clear, and fixing them first gives the Architect the PR as reviewed.
- `behavior` and `design` items, QA failures and failing checks: the
  Architect.
- `answer` and `decline`: T7 replies; a `decline` needs the human's OK in T4.

**Merge first.** The base branch goes in before anything else, so every
stage works on current code. Run `review-rounds.md` R4 § Check a merge
before the question, then list the conflicts without touching the worktree:
`git -C <worktree> merge-tree --write-tree --name-only HEAD origin/<PR base>`.
`git show <tree>:<path>` shows a file with its conflict markers.

- No conflicts, or conflicts only in lockfiles, generated files, imports
  or lines one side only moved or reformatted: the merge is item 1 of the
  first Wrap-up, with how to resolve each conflicted file.
- A conflict inside logic the PR changes: the Architect plans how to keep
  both sides, and the merge is the Coder's first block.

## T4. Ask once, then run

Show the conditions table, the chain and its price: no takeover has been
measured yet, so quote the full ticket chain (Architect, Coder, Hardener,
Tester, Reviewer, Wrap-up), $7–21 and 25–105 minutes active over 15 runs,
median about $14, plus about $1–2 for the first Wrap-up. Prefer rows with a
`takeover` field in `~/.team-lead/performance/index.jsonl` once they exist.
Then, in **one** `AskUserQuestion` call, ask each `decline`, each `answer`
you cannot answer from the code, and the derived acceptance criteria, each
with your recommendation. Nothing to ask: say the chain and its price in
one line and start.

## T5. Run the chain

Write `handoff-common.md` (`handoff.md`) with its *Takeover* section:
the PR, the takeover start, the note and the conditions table.
Every stage runs as in § 3 to § 9, with these changes:

- **First Wrap-up.** Write its list to `takeover-fixes.md`, numbered as in
  § 8, and spawn `team-wrapup` with the description
  `Wrap-up comments — <TICKET_ID>` and the report file
  `reports/wrapup-comments.md`. After a merge, check that
  `git diff origin/<PR base> HEAD --stat` names the same files as before
  it, then recompute **Base commit** and rewrite `handoff-common.md`.
- **Architect.** Its handoff's *Your task*: map what the PR already does
  against each acceptance criterion, and plan how to close every open
  condition routed to it while keeping what the PR already gets right. It
  answers `Code needed: no` when the PR already meets them; then skip the
  Coder. Its escalations go to the human as in § 3.
- **Coder.** As § 4–7. After a merge block, check the diff stat and
  recompute the base as for the first Wrap-up.
- **Hardener, Tester, Reviewer.** As § 4–7, against the PR's base. Their
  *Your task* says: this is a takeover, cover the whole PR.
- **Report checks.** Run `check-stage.sh` with the **takeover start** in
  place of the base, so the earlier agent's commits are not checked as
  the team's. A co-attribution line in one of them is not a finding.
- **Triage and final Wrap-up.** As § 8 and § 9. A review finding on code
  the earlier agent wrote counts the same as one on the team's: the PR is
  the team's now.
- **Final sanity check.** As § 10, plus: every condition in `conditions.md`
  is met or answered, each with the commit or report that shows it.

## T6. Push

`git -C <worktree> push origin <head>`. Never force-push; a rejected push
means the remote moved: stop and tell the human. Save the old body as
`takeover-pr-body-before.md` (`gh pr view <PR> --json body -q .body`), then
rewrite it for the whole PR in the format of § 10 (or the repo's template
and the profile's *Conventions*), with the conditions closed under
*What changed*, and `gh pr edit <PR> --body-file` it. Register the PR with
`link_pull_request` when that tool is available.

## T7. Replies

Answer every review item in `conditions.md`, on the PR, in plain words: what
changed and the commit (`abc1234`), the answer, or the reason it did not
change. Write them to `takeover-replies.md` first, then post each:

- a line-comment thread: `gh api graphql -f query='mutation($id:ID!,$body:String!){addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$id,body:$body}){comment{url}}}' -F id=<thread id> -f body=<reply>`;
- a review or PR comment: one `gh pr comment <PR> --body-file <file>` that
  quotes each comment it answers and links it.

Do not resolve threads: the reviewers resolve their own in their next pass.
Add each posted reply's URL to `takeover-replies.md`.

## T8. Slack

Skip with `--no-slack`, when a profile's *Conventions* say `Slack: none`,
or when the PR is still a draft (the final message then says to mark it
ready and post it). Use the profile's channel, else `C0BULBDLXUK`. Load
`mcp__claude_ai_Slack__slack_search_public_and_private`,
`mcp__claude_ai_Slack__slack_read_thread` and
`mcp__claude_ai_Slack__slack_send_message` with `ToolSearch`.

1. **Find the PR's post.** Search the channel for the PR number:
   `keywords: ["<number>"]`, `filters: in:<#<channel>>`,
   `include_bots: true`, `sort: timestamp`. A hit inside a thread carries
   `thread_ts` in its permalink. The post is the thread's parent whose text
   links this PR (`/pull/<number>`); read it with `slack_read_thread`.
2. **Found:** list the thread's replies whose author is marked `[BOT]`,
   once each by user ID. Reply in the thread with only their mentions and
   `second pass`, for example `<@U0C2ZTAL8M7> <@U0ABCDEF12> second pass`.
   A thread with no bot replies gets `second pass` alone.
3. **Not found:** post the PR fresh, with the message in § 10. The review
   bots pick it up from there.

Save the post's or reply's link as `slack` in `run.json`. If Slack fails,
say so; the PR still stands.

## T9. Assess

As § 11, with `Takeover: yes`, the run's `started_at`, and the PR's base as
the base commit.

**Final message**: as § Final message, plus each condition with what
happened to it (closed in `<sha>`, answered, declined), the path to
`takeover-replies.md` and how many replies were posted, and the Slack
link with whether it was a second-pass request or a fresh post.

**Resume** with `--takeover <PR> --from <stage>`: read `run.json`,
`conditions.md` and `handoff-common.md`, keep the conditions, the takeover
start and the base, and continue at that stage (`wrapup-comments`,
`architect`, `coder`, `hardener`, `tester`, `reviewer`, `wrapup`, `pr` or
`assess`; `pr` covers T6 to T8). Later review rounds on this PR use
`--round` as usual.
