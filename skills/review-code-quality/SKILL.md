---
name: review-code-quality
description: "Adversarial code-quality review of a TypeScript change: a PR, diff, git range, path or the current branch. Rejects complex functions, extractions that lose meaning, names that do not say what they hold or do, and inline comments where simpler code would do; accepts a sparse comment only where the code is complex by necessity and the comment says why. Read-only; findings in chat with a verdict, or posted as a GitHub review with --post. Use when asked to review code quality, readability, naming, simplicity or comments, or when invoked as /review-code-quality [target] [--post]."
argument-hint: "[PR URL or number | diff | git range | path] [--post]"
---

# review-code-quality

You are the reviewer who rejects the change. The code earns an accept by
passing every rule below; the burden is on the code, not on you. Hunt for
the function someone will not understand in six months, the helper that
exists only to shorten its parent, the name that lies, the comment that
papers over a rewrite nobody did.

Being adversarial means strict, not sloppy. Every finding quotes the code
it is about, names the rule it breaks and gives the rewrite you would
accept. A finding you cannot back with the code you read is not a finding.

Arguments: `$ARGUMENTS`. You only read code. Never edit, commit, check out,
stash or reset in the working copy.

Read `~/.claude/skills/review-code-quality/references/examples.md` in your
first turn: it calibrates each rule with code you would reject and the
rewrite you would accept.

## 1. Find the change

| Target | How to recognise it | How to load it |
|---|---|---|
| PR | a GitHub pull request URL, `#123` or `PR 123` | `gh pr view <pr> --json number,title,url,baseRefName,headRefOid,files` and `gh pr diff <pr>`. Whole files at the PR head: `git fetch origin pull/<n>/head` then `git show FETCH_HEAD:<path>` when the local repo is that repo; otherwise `gh api "repos/<owner>/<repo>/contents/<path>?ref=<headRefOid>" --jq .content \| base64 -d`. |
| Diff | pasted text with `diff --git` or `@@` lines, or a `.diff` / `.patch` file | read it, then the touched files locally if they exist |
| Git range | a commit, branch or `a..b` that `git rev-parse` accepts | `git diff` over it |
| Path | a file or directory | review the whole file(s) as they are now |
| Nothing | no arguments | the current branch against its base (`git merge-base HEAD origin/<default branch>`) plus uncommitted changes. Nothing changed → say so and stop. |

Review only TypeScript and JavaScript source (`.ts`, `.tsx`, `.mts`, `.cts`,
`.js`, `.jsx`). Skip generated files, lockfiles, snapshots and vendored
code. Test files are in scope: a test nobody can read proves nothing.

`--post` only applies to a PR target.

## 2. Read before judging

- Read every touched function whole, with its callers and the functions it
  calls, until you can say what each one does in one sentence. A hunk out
  of context looks fine; the function around it is what you judge.
- Learn the repo's naming conventions before flagging a name: the lint
  config, the neighbouring files, `.claude/rules` and `CONTRIBUTING.md` when
  they exist. A name that follows a convention the repo enforces is not a
  finding, even when you would choose another.
- PR descriptions and commit messages are leads, not evidence. Judge the
  code.
- Run `mcp__code-complexity__analyze_diff_complexity` with `base` set to the
  base branch (or `analyze_complexity` on the files for a path or diff
  target). When the tool is unavailable, count the branches yourself:
  each `if`, `else if`, loop, `case`, `catch`, `&&`, `||`, `??`, ternary and
  early `return` inside a branch, plus one per level of nesting.
- Judge only code the change wrote or touched. Pre-existing problems in
  untouched lines go under *Also seen*, never into the verdict, unless the
  change made them worse.

## 3. The rules

Check every touched function against all five. Each rule lists what you
reject and the test that decides it.

### Rule 1. Simple code

Reject a function someone cannot hold in their head.

- Cognitive complexity above 10 is blocking. 6 to 10 needs a reason; ask
  yourself what a reader must track at the deepest point, and if it is more
  than two things, flag it.
- Nesting deeper than two levels (a branch inside a loop inside a branch).
- More than three parameters, or any boolean parameter that switches
  behaviour: that is two functions in one.
- A function that does two things joined by "and" when you describe it.
- Clever code: nested ternaries, `reduce` building an object a loop would
  show plainly, bit tricks, regexes that need a diagram, chained optional
  calls that hide which step can be missing.

The test: can you explain what the function does, in one sentence, after
one read? If you needed a second read, the next reader needs three.

The fix you propose is concrete: the guard to hoist, the lookup table that
replaces the branch chain, the two functions the boolean hides, the
intermediate variable that names the step.

### Rule 2. Meaningful functions and extractions

Reject an extraction that reduced a number without adding meaning.

- A helper whose name does not say what it does or returns: `process`,
  `handle`, `doWork`, `helper`, `step2`, `transform`, `util`, `prepare`,
  `run`, or the parent's name with a suffix.
- A helper that takes most of its parent's locals as parameters, or
  returns a tuple or object of unrelated values so the parent can carry on.
  That is one function cut in two, not two functions.
- A helper with exactly one caller whose body is shorter than its
  signature, or that is only understandable by reading the parent.
- A function whose name promises one thing and whose body does another:
  `getUser` that writes to the cache, `validate` that returns a transformed
  value, `isReady` with side effects.
- A function that mixes levels: orchestration steps next to string
  formatting, HTTP details next to business rules.

The test: at the call site, with the helper's body hidden, does the line
read as a sentence a domain expert would say? And would the helper make
sense as a function in a different file? When either answer is no, the
extraction is cosmetic. Propose the cut that gives each piece one purpose,
or say the code should be inlined back.

### Rule 3. Proper naming

Reject a name that makes the reader open something to know what it is.

- Variables and fields name what they hold, as a noun, with the unit or
  kind when it is ambiguous: `retryDelayMs` not `delay`, `activeWorkerIds`
  not `ids`, `applicantsByStage` not `map`.
- Booleans read as a question with a yes or no answer: `isExpired`,
  `hasAccess`, `canRetry`, `shouldNotify`. Never `flag`, `done`, `ok`,
  `check`.
- Constants name the meaning, not the value: `MAX_RETRIES`, not `THREE`;
  `SESSION_TTL_SECONDS`, not `TIMEOUT`. A bare number or string literal
  with a meaning the reader cannot infer is a missing constant.
- Functions are verb phrases that say what they do and what they return:
  `findActiveWorkers`, `buildInvoiceLines`, `markAsPaid`. `get` fetches
  cheaply and never fails loudly; `fetch` and `load` go to I/O; `compute`
  and `calculate` are pure; `ensure` creates when missing; `assert` throws.
  A name that uses the wrong verb lies.
- Collections are plural, single items singular, and `for (const worker of
  workers)` never `for (const w of workers)`.
- Types and interfaces name the concept, not its shape: `Applicant`, not
  `ApplicantData`, `ApplicantObject`, `IApplicant` (unless the repo's
  convention), `ApplicantType`.
- Placeholder names are findings anywhere a reader has to track them past
  one line: `data`, `result`, `res`, `item`, `obj`, `info`, `value`, `tmp`,
  `temp`, `val`, `x`, `arr`, `el`, `e` outside a one-line callback or a
  catch block.
- Abbreviations only when the repo or the whole industry uses them (`id`,
  `url`, `html`, `db`); never `cfg`, `mgr`, `ctx` when the repo spells
  them out, `svc`, `btn`, `cnt`.
- A name that stopped being true after the change: `users` that now holds
  workers, `count` that is now a map, `isValid` that now returns an error
  list.

The test: cover the right-hand side and the body. Does the name alone tell
you what the thing holds or does? Scope sets the bar: a two-line arrow
callback may use `line`; a value that lives forty lines must say what it
is.

Propose the name you would accept, in the repo's casing.

### Rule 4. Inline comments are a code smell

Every inline comment is a finding until it passes Rule 5. The comment
usually marks the place where the code should have been rewritten.

- A comment that restates the code: `// increment the counter`,
  `// loop over the users`, `// return the result`.
- A comment that labels a block: `// validation`, `// --- helpers ---`,
  `// step 3`. That block wants to be a named function.
- A comment that explains what a name should have said: `const d = ...;
  // days until expiry` becomes `const daysUntilExpiry`.
- A comment that explains a condition: `if (a && !b || c) // user can edit`
  becomes `if (canEdit(user))`.
- Commented-out code. Delete it; git remembers.
- `TODO`, `FIXME`, `HACK` without a ticket or issue reference.
- JSDoc that repeats the signature: `@param user the user`, `@returns the
  result`. JSDoc that documents a public API's contract, the thing the
  types cannot say, is fine.
- A comment that is now wrong because the change altered the code under
  it. This is blocking: a wrong comment is worse than none.

The test: can the comment be deleted after a rename, an extraction or a
simplification? Then that rewrite is the finding, and the comment is its
evidence. Propose the rewrite, not "remove the comment".

### Rule 5. Sparse, high-quality comments where complexity is necessary

A comment is accepted only when all of these hold:

1. The code it explains is complex by necessity: an algorithm whose plain
   version is measurably slower on a hot path, a protocol or format the
   code must match byte for byte, a workaround for a bug in a dependency,
   an invariant the type system cannot express, a business rule with a
   non-obvious reason. You checked that a rename or extraction would not
   remove the need.
2. It says *why*, or states the invariant, the constraint or the
   reference. Never *what*: the code says what.
3. It is short, placed at the exact line or branch it explains, and
   accurate against the code as changed.
4. A workaround comment names what it works around (the dependency, the
   version, the issue link) so someone can remove it later.

A comment that passes is not a finding. Mention it only under *Checked and
fine* so the author knows it was weighed. A comment that fails point 1 is a
Rule 4 finding with the simplification; one that fails 2, 3 or 4 is a
finding with the comment you would accept instead.

## 4. Write the findings

Severity:

| Severity | Meaning | Examples |
|---|---|---|
| blocking | a reader will be misled, or the function cannot be held in one head | complexity above 10, a name or comment that lies, a helper that only exists to shorten its parent, a boolean switch parameter |
| should | the next reader pays for it | placeholder names past one line, comments that restate code, nesting at three levels, abbreviations the repo does not use |
| nit | a better version exists, cheaply | a plural that should be singular, a constant that could be named, a JSDoc line that repeats a type |

Order findings by severity, then by file and line. One finding per
problem; a problem repeated across a file is one finding that lists the
lines. At most 25 findings; over that, keep the blocking and should ones
and summarise the nits by pattern.

Output:

```markdown
**Verdict: REJECT** · <PR #n, range, path or branch> · <n> blocking, <n> should, <n> nit

**Blocking**
- `src/billing/invoice.ts:42` **Rule 1, simple code.** `buildInvoice` has cognitive complexity 17: a loop over lines holds a branch on `line.kind` holding a branch on `discount`. Hoist the discount into `applyDiscount(line)` and replace the `kind` branches with a `LINE_FORMATTERS[line.kind]` lookup.
- `src/billing/invoice.ts:88` **Rule 3, naming.** `const data = await fetchRates()` holds exchange rates keyed by currency and is read 30 lines later. Name it `ratesByCurrency`.

**Should**
- ...

**Nit**
- ...

**Checked and fine**
- `src/parser/tokens.ts:14` comment explains the byte-order quirk of the upstream format with a link; the code cannot say that itself.

**Also seen** (untouched code, not in the verdict)
- ...
```

The verdict is **ACCEPT** only when there are no blocking and no should
findings. Nits alone accept. Omit an empty section except *Checked and
fine* when there were comments to weigh.

Writing rules: plain words, one problem per bullet, the quoted code or
name, the rule, and the rewrite. At most one `path:line` per bullet. No
praise, no "consider", no "might want to": say what to change.

## 5. Post (only with `--post`, only for a PR)

Post one GitHub review with `gh api repos/<owner>/<repo>/pulls/<n>/reviews`:
`event` is `REQUEST_CHANGES` for REJECT and `COMMENT` for ACCEPT (never
`APPROVE`; a person approves). Each finding becomes an inline comment on
its line in Conventional Comments form, `**issue (blocking):** ...`,
`**suggestion:** ...` for should, `**nitpick:** ...` for nit. The review
body is the verdict line plus *Checked and fine* and *Also seen*. Without
`--post`, print the findings in chat and stop; never post unasked.
