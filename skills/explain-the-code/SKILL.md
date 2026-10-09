---
name: explain-the-code
description: "Explain a PR, diff, file, git range or the current branch's changes in short plain-language bullets the human reads in 30-60 seconds (up to 3 minutes for large changes): a dictionary mapping the names people and agents use to the code's names, what was done, how it works, the problem each part solves, the tradeoffs and where to look when it breaks. Then quiz the human on the points they need to triage and build on the code, and re-explain any gaps once. Invoke as /explain-the-code [PR URL | diff | file | git range] [what to focus on]."
argument-hint: "[PR URL or number | diff | file path | git range] [what to focus on]"
disable-model-invocation: true
---

# explain-the-code

The human directs AI agents that write most of the code. They lose track of
what changed, and reading long summaries slows them down. Your job: make
them understand the change in under a minute, then prove they did with a
short quiz.

Arguments: `$ARGUMENTS`. You only read code. Never edit, commit, switch
branches or check out a PR in the human's working copy.

## 1. Find what to explain

The first words name the **target**; everything after it is the **focus**.

| Target | How to recognise it | How to load it |
|---|---|---|
| PR | a GitHub pull request URL, `#123` or `PR 123` | `gh pr view <pr> --json number,title,body,url,baseRefName,headRefOid,files,commits` and `gh pr diff <pr>`. Skim `gh pr view <pr> --comments` for stated tradeoffs. To read whole files at the PR's head, run `git fetch origin pull/<n>/head` then `git show FETCH_HEAD:<path>` when the local repo is that repo; otherwise `gh api "repos/<owner>/<repo>/contents/<path>?ref=<headRefOid>" --jq .content \| base64 -d`. |
| Diff | pasted text with `diff --git` or `@@` lines, or a `.diff` / `.patch` file | read it, then read the touched files locally if they exist |
| Git ref or range | a commit, branch or `a..b` that `git rev-parse` accepts | `git log` and `git diff` over it |
| File | a path, or a bare name such as `taskFlowWorkers.proxy.ts` | resolve a bare name with `git ls-files \| grep -E '(^\|/)<name>$'`; several matches → ask which with `AskUserQuestion`. Explain what the file does now. If it has uncommitted or branch changes, cover those too and say so. Several files are fine. |
| Nothing | no arguments | the current branch against its base (`git merge-base HEAD origin/<default branch>`) plus uncommitted changes. Nothing changed → ask what to explain. |

The **focus** is a question or topic, such as `How does a worker get a flow
assigned and unassigned`. Explain and quiz only what answers it, plus what
it depends on to make sense. No focus → the whole target.

## 2. Understand it before writing

- Read the changed code, then enough of its callers and of what it calls to
  describe the flow end to end. Stop at code the change does not affect.
- Every statement must rest on code you read. PR descriptions, commit
  messages and agent summaries are leads, not proof; agents write them and
  they drift from the code. When the code contradicts them, the code wins,
  and say so in a bullet: "The PR says X; the code does Y."
- The *why* comes from the ticket, PR, commits or code comments. When you
  can only infer it from the code, write "probably".
- Note what triggers the code, the order of its steps, what it writes and
  where, what happens on failure, retry or empty input, which rule must
  stay true, and what a person would see when it breaks. The quiz is built
  from these.
- For a large PR, split the reading by area across `Explore` subagents run
  in parallel. Ask each for its area's flow, failure points and tradeoffs
  with `path:line`. Write the explanation yourself.

## 3. Build the dictionary

People and agents call code objects by names the code does not use: "the
enrollment" for `TaskFlowWorker`. The dictionary maps those names to the
code before the human meets them.

- Read `~/.claude/skills/explain-the-code/glossary.md` for known names in
  this repo.
- Collect names for code objects used in the PR title and body, commit
  messages, code comments, review threads and this conversation that differ
  from the code's own names.
- One entry per name: `"the enrollment"` → `TaskFlowWorker` (service-todo):
  what it is in business terms, in one line. Add plain meanings for any
  technical term the explanation cannot avoid.
- Skip names equal to the code name. At most 6 entries; no entries → no
  section.
- If the human corrects or adds a name during the session, offer to add it
  to the glossary file.

## 4. Write the explanation

Pick the budget before writing:

| Budget | When | Words after the dictionary | Quiz |
|---|---|---|---|
| Standard, 30-60 s | default | at most 200 | 3-5 questions |
| Large, up to 3 min | the change spans several modules or flows that interact, or the focus asks how they interact, and 200 words would drop something needed to triage it | at most 600 | 5-8 questions |

Output, in this order:

```markdown
**<what this explains>** · <PR #n, file, range or branch> · ~<seconds> s read

**Words**
- "the enrollment" → `TaskFlowWorker` (service-todo): one worker in one task flow, with counts of their tasks by status.

**What it does**
- <1-2 bullets: what changed and why, in one breath>

**How it works**
1. <step: what happens, which part does it, and the problem that part solves>

**Tradeoffs**
- <what was given up or left out, and what that means in practice>

**If it breaks**
- <symptom> → <where to look> (`path:line`)
```

Writing rules:

- Plain everyday words. Short sentences, active voice. No unexplained
  acronyms or framework-speak.
- One idea per bullet, at most 25 words.
- Call code objects by their code name in backticks. Never invent a
  nickname; the dictionary holds the other names.
- Be concrete: real fields, values and conditions ("when `status` is
  `rejected`"), never "handles edge cases".
- At most one `path:line` per bullet, only where it helps find the code.
- No praise, no filler, no "this PR introduces".
- Count the words before sending. Over budget → cut repetition, background
  and nice-to-know detail first. Never cut a failure point.

## 5. Quiz

Send the quiz in the same turn, right after the explanation.

**Pick the points.** The facts the human cannot miss if they are to
triage a problem in this code or build on it: what triggers it, the order of
steps, where data is written, failure and edge-case behavior, the rule that
must stay true, the visible effect of a tradeoff. Never names, line numbers
or trivia. Each question tests one point, and the explanation must contain
its answer.

**Write each question.**

- A short scenario: "A worker finished every task but still shows *in
  progress*. Which part most likely did not run?"
- 3 or 4 options of similar length and style. One is correct. The others
  are realistic misunderstandings: the alias confused with another object,
  steps in the wrong order, the wrong part blamed.
- Spread the correct answer across positions. Never mark an option as
  recommended. No "all of the above".
- Before asking, note for yourself each question's correct option and the
  point it tests. Do not show them.

**Ask.** Use `AskUserQuestion`: up to 4 questions per call, headers `Q1`,
`Q2`..., single choice. More than 4 → a second call once the first returns.
Grade only after every answer is in. Without `AskUserQuestion`, print the
questions numbered with lettered options, ask for a reply like `1b 2a 3c`,
and end the turn.

**Grade.** A typed answer counts only if it states the same fact. "I don't
know" is wrong.

- All correct → one line: `All <n> correct.` Done.
- Any wrong → round 2.

## 6. Round 2, once

1. Score line: `<k>/<n> correct.`
2. For each wrong answer, name the misunderstanding it shows, in one
   line: "You picked B, so you think the summary is written before the
   enrollment. It is written after."
3. A new explanation of only those gaps, at most 150 words. Explain them
   from a new angle: walk through one concrete case with real values
   instead of repeating the first wording.
4. A new quiz: one fresh question per missed point, with a different
   scenario testing the same fact.

All correct → `Gaps closed. All <n> correct.` Done.

Any wrong again → give the correct answer to each miss in one line, then
stop with:

```markdown
# NOT UNDERSTOOD YET. DO NOT BUILD ON THIS CODE.

You missed the same key points twice: <point>, <point>.
Without them you cannot triage a problem in this code.

Run it again on the PR, focused on the gaps:
`/explain-the-code <PR URL> <the missed points, as one question>`
```

When the target was not a PR, find the PR behind it (`gh pr view --json
url` for the current branch, or `gh pr list --state all --search <sha>` for
the last commit touching a file) and put its URL in the command. No PR
found → use the original target.

There is no round 3.
