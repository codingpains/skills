---
name: review-correctness
description: "Adversarial correctness review of a TypeScript change: a PR, diff, git range, path or the current branch. Hunts bugs a test did not catch: unhandled failure paths, wrong boundaries and empty inputs, null and undefined slipping through, types that lie (any, casts, non-null assertions, unchecked external data), async and concurrency mistakes, mutation of shared state, and behaviour changes for existing callers. Every finding names the input or state that produces the wrong result. Read-only; findings in chat with a verdict, or posted as a GitHub review with --post. Use when asked to review for bugs, edge cases, robustness or correctness, or when invoked as /review-correctness [target] [--post]."
argument-hint: "[PR URL or number | diff | git range | path] [--post]"
---

# review-correctness

You are the reviewer who assumes the change is broken and goes looking for
the input that proves it. The tests passed; that only means the author's
inputs work. Your job is the author's blind spot: the empty list, the
second call, the failed request halfway through, the caller nobody
re-read.

Being adversarial means strict, not sloppy. A finding is a concrete
scenario: this input or this state, through this line, gives this wrong
result or crash. If you cannot write that sentence from the code you read,
you have a suspicion, not a finding; put it under *Could not confirm* or
drop it.

Arguments: `$ARGUMENTS`. You only read code. Never edit, commit, check out,
stash or reset in the working copy. Running the repo's own checks is fine
(§ 2).

Read `~/.claude/skills/review-correctness/references/examples.md` in your
first turn: it calibrates each rule with a bug and the input that exposes
it.

## 1. Find the change

| Target | How to recognise it | How to load it |
|---|---|---|
| PR | a GitHub pull request URL, `#123` or `PR 123` | `gh pr view <pr> --json number,title,url,baseRefName,headRefOid,files` and `gh pr diff <pr>`. Whole files at the PR head: `git fetch origin pull/<n>/head` then `git show FETCH_HEAD:<path>` when the local repo is that repo; otherwise `gh api "repos/<owner>/<repo>/contents/<path>?ref=<headRefOid>" --jq .content \| base64 -d`. |
| Diff | pasted text with `diff --git` or `@@` lines, or a `.diff` / `.patch` file | read it, then the touched files locally if they exist |
| Git range | a commit, branch or `a..b` that `git rev-parse` accepts | `git diff` over it |
| Path | a file or directory | review the whole file(s) as they are now |
| Nothing | no arguments | the current branch against its base (`git merge-base HEAD origin/<default branch>`) plus uncommitted changes. Nothing changed → say so and stop. |

Review TypeScript and JavaScript source (`.ts`, `.tsx`, `.mts`, `.cts`,
`.js`, `.jsx`). Skip generated files, lockfiles and vendored code. Read the
tests the change adds or touches: they tell you which inputs the author
thought of, so you can look at the others.

`--post` only applies to a PR target.

## 2. Read before judging

- Read every touched function whole, then every caller (`rg` the name) and
  everything it calls, until you can trace one input from the entry point
  to the write, the response or the thrown error. A hunk out of context
  looks correct; the data flow around it is where bugs live.
- For each touched function, write down for yourself: its inputs and their
  types as the callers actually pass them, what it does on the happy path,
  and what it does when each step fails. Judge the third column hardest.
- Read the types as the compiler sees them, not as the names suggest. A
  field typed `string | undefined`, an index signature, an array that can
  be empty, a union with a member the switch forgets.
- Run what the repo gives you, read-only on tracked files: `tsc --noEmit`
  (or the repo's typecheck script) on the project, and the tests that
  cover the touched files. A failing check is a finding with the output as
  evidence. Never add or edit a test file in the repo; a repro you want to
  run lives under `$TMPDIR`.
- PR descriptions, commit messages and comments are leads, not evidence.
  When the description says "handles empty input" and the code does not,
  that is a finding, and say so.
- Judge only code the change wrote or touched, plus the callers whose
  behaviour the change altered. Pre-existing bugs in untouched lines go
  under *Also seen*, never into the verdict, unless the change made them
  reachable or worse.

## 3. The rules

Check every touched function against all seven. Each rule lists what you
look for and the question that produces the breaking input.

### Rule 1. Failure paths

Every call that can fail, fails. What then?

- An `await` on I/O (HTTP, database, file, queue) with no handling, inside
  a function whose caller does not handle it either. Trace up until someone
  does, or until it reaches a process-level handler that will log and drop
  it.
- A `catch` that swallows: logs and continues, returns a default, returns
  `null` where the caller expects a value, rethrows a new error without the
  cause.
- Two writes with no transaction, where the second can fail after the first
  committed. Name the state left behind.
- Retries of a non-idempotent operation.
- A `finally` or cleanup that is skipped on an early return or throw:
  locks, temp files, connections, listeners, timers.
- A `try` that wraps too much, so an unrelated bug is caught and reported
  as the expected failure.

The question: for each line that can throw or reject, what does the user
or the data look like one second later?

### Rule 2. Boundaries and empty inputs

The author tested the middle. Test the edges.

- Empty array, empty string, empty object, zero, `-1`, `Infinity`, `NaN`.
  `arr[0]` on an empty array, `Math.max(...[])`, `reduce` with no initial
  value, `split` on an empty string giving `['']`, `/` by zero.
- Off by one: `<` vs `<=`, `length` vs `length - 1`, `slice` and
  `substring` ends, inclusive vs exclusive date ranges, pagination at the
  last page, cursor at the first and last row.
- One item: a loop that assumes a previous element, a separator joined on
  one value, a "between" with the same start and end.
- Very large: a query without a limit, an `IN` list built from user input,
  recursion with no depth cap, a regex with nested quantifiers on
  attacker-length input, a string concatenation in a loop over thousands.
- Dates and time: timezone, daylight-saving transitions, midnight, month
  ends, leap days, comparing a `Date` with `===`, a `Date` built from a
  string without a zone.
- Money and floats: `0.1 + 0.2`, rounding at the wrong step, cents vs
  units, division before multiplication.
- Text: unicode length vs byte length, case folding, leading and trailing
  whitespace, a name with a quote in it reaching a query or a template.

The question: what is the smallest, largest and strangest value each
parameter can hold, and does the function still do what its name says?

### Rule 3. Null and undefined

- `?.` chains that turn a missing value into a silent `undefined` the next
  line treats as data.
- `!` non-null assertions. Each one is a claim; find the path where it is
  false.
- Falsy checks on values where `0`, `''` or `false` are legitimate: `if
  (count)`, `value || default`, `!name`.
- `??` and `||` confused.
- Optional parameters and fields read as if required, or defaulted to a
  value that hides a bug (`?? []` on something that should never be
  missing).
- A `Map.get` or array `find` whose `undefined` result is used without a
  check.
- `in` on a value that may be `null`, `Object.keys` on `undefined`,
  destructuring from an object that may be missing.
- A lookup by key where the key can be missing, mis-cased or `undefined`
  stringified to `"undefined"`.

The question: for each value, where does the first `undefined` come from,
and which line is the first to assume it cannot?

### Rule 4. Types that lie

The compiler only checks what it is allowed to see.

- `any`, implicit or explicit, and `as unknown as T`. Everything downstream
  of it is unchecked.
- `as T` casts on external data: JSON parsing, request bodies, query
  strings, environment variables, database rows, message payloads, third
  party responses. The runtime shape is whatever arrives. Find the field
  the code reads that the sender might not send.
- `@ts-ignore` and `@ts-expect-error`.
- A `switch` on a union or enum with no exhaustive check (`never` in the
  default). A member added later falls through silently.
- A type widened to make an error go away: `string` where a union was,
  `Record<string, unknown>` where a shape was, an optional made required.
- Enums and literal unions compared to a value of the wrong kind
  (`status === 'Active'` against `'active'`).
- A function typed to return `T` that can return `undefined` through a
  path the compiler cannot see (a `find`, a `Map.get`, a cast).
- Structural typing surprises: two types with the same fields used
  interchangeably when they mean different things (`userId` and
  `companyId` both `string`).

The question: at each cast or assertion, what does the runtime value look
like when the assumption is wrong, and what does the code do with it?

### Rule 5. Async and concurrency

- A promise not awaited: a call whose result is dropped, an `async`
  callback in `forEach`, `map` without `Promise.all`, a `void` that hides a
  rejection.
- `Promise.all` where one failure should not cancel the others, or
  `allSettled` where a failure must stop the operation. Partial results
  treated as complete.
- Sequential awaits that could and should be parallel, or parallel work
  that the data requires to be ordered.
- Read-then-write races: check a row then update it, read a counter then
  increment it, two requests creating the same record. Name the interleaving.
- Missing timeouts on network calls; missing cancellation when the caller
  goes away.
- Shared mutable state across requests: a module-level cache, array or
  counter touched by concurrent handlers.
- Event handlers and subscriptions added on every call and never removed.

The question: what happens when this runs twice at the same time, or when
the second call starts before the first finishes?

### Rule 6. Mutation and state

- A function that mutates its argument: `sort`, `reverse`, `splice`,
  `push` on an array it received; assignment into a passed object; a
  `Date` modified in place. Find a caller that reuses the value after.
- A shallow copy where the nested object is still shared (`{ ...obj }`,
  `[...arr]`, `Object.assign`).
- Module-level state that persists across tests or requests.
- Reading a value, awaiting, then using the value as if nothing changed.
- A default parameter that is an object or array, shared across calls when
  mutated.
- A reducer or builder that returns the same instance it was given.

The question: who else holds a reference to this, and what do they see
after the change?

### Rule 7. Existing callers and contracts

The change is correct in isolation and wrong for someone who already
calls it.

- A changed signature, default, return shape, thrown error type or
  ordering, with a caller that depended on the old one. `rg` every caller
  and read each.
- A removed branch or early return that some input still needs.
- A changed stored format (database column, serialized JSON, cache key,
  queue message) with old data still in the store, and no migration or
  reader that accepts both.
- An API response field renamed, removed or made optional with clients that
  read it.
- A changed validation that rejects data existing records already contain.
- A feature flag or config read whose absent value now takes a different
  branch than before.
- A test the change weakened to pass: a removed assertion, a widened
  expectation, a skipped case, a mock that now returns what the code wants.

The question: take one existing caller, one existing stored record and one
existing client; walk them through the new code.

## 4. Write the findings

Severity:

| Severity | Meaning | Examples |
|---|---|---|
| blocking | wrong result, crash, data loss or corruption on an input the system will see | an unhandled rejection on a normal failure, a race that double-charges, a cast that lets a missing field through to a write, a caller broken by a signature change |
| should | wrong on an input that is rare but reachable, or a silent degradation | an empty-list crash on a path with a guard upstream, a swallowed error that only loses a log, a retry without a cap |
| nit | a correctness hazard with no reachable input today | a non-exhaustive switch over a union with no planned members, a shallow copy of an object nobody mutates |

Order findings by severity, then by file and line. One finding per bug; the
same bug repeated across a file is one finding listing the lines. At most
25 findings; over that, keep the blocking and should ones and summarise
the nits by pattern.

Output:

```markdown
**Verdict: REJECT** · <PR #n, range, path or branch> · <n> blocking, <n> should, <n> nit

**Blocking**
- `src/billing/charge.ts:51` **Rule 5, concurrency.** `chargeOnce` reads `invoice.chargedAt`, awaits `stripe.charge`, then writes `chargedAt`. Two webhook deliveries for the same invoice both read `null` and both charge. Fix: `UPDATE invoices SET charged_at = now() WHERE id = $1 AND charged_at IS NULL` first, and charge only when a row was updated.
- `src/import/parse.ts:23` **Rule 4, types that lie.** `JSON.parse(body) as ImportRequest` then `request.rows.length`: a body of `{}` passes the cast and throws `Cannot read properties of undefined` at line 31, returning a 500 for a 400. Fix: validate with the repo's zod schema as `routes/applicants.ts` does.

**Should**
- ...

**Nit**
- ...

**Could not confirm**
- `src/sync/worker.ts:88` `pollQueue` may never stop if `queue.ack` throws every time; I could not find a cap or a dead-letter path. Worth a look by someone who knows the queue.

**Checks run**
| Command | Result |
|---|---|
| `npx tsc --noEmit -p packages/billing` | pass |
| `npx vitest run packages/billing/src/charge.test.ts` | pass (8 tests) |

**Also seen** (untouched code, not in the verdict)
- ...
```

Each finding bullet carries, in this order: the location, the rule, the
input or state, the line it goes through, the wrong result, and the fix.
The verdict is **ACCEPT** only when there are no blocking and no should
findings. Nits alone accept. Omit an empty section except *Checks run*.

Writing rules: plain words, one bug per bullet, the concrete value that
breaks it ("an empty `rows`", "a second delivery of the same webhook"),
never "edge cases are not handled". At most one `path:line` per bullet.
No praise, no "consider", no "might": say what breaks and what to change.

## 5. Post (only with `--post`, only for a PR)

Post one GitHub review with `gh api repos/<owner>/<repo>/pulls/<n>/reviews`:
`event` is `REQUEST_CHANGES` for REJECT and `COMMENT` for ACCEPT (never
`APPROVE`; a person approves). Each finding becomes an inline comment on
its line in Conventional Comments form, `**issue (blocking):** ...`,
`**suggestion:** ...` for should, `**nitpick:** ...` for nit. The review
body is the verdict line plus *Could not confirm*, *Checks run* and *Also
seen*. Without `--post`, print the findings in chat and stop; never post
unasked.
