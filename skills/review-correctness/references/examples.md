# Examples per rule

Each example: the code, the input that breaks it, and the fix. A finding
in a review reads like the "Breaks on" line.

## Rule 1. Failure paths

```ts
async function publish(post: Post) {
  await db.posts.update(post.id, { status: 'published' });
  await search.index(post);          // can fail
}
```

Breaks on: search is down. The post is `published` in the database and
missing from search, forever; nothing retries. Fix: index inside the same
unit of work, or write an outbox row and index from it.

```ts
try {
  return await fetchProfile(id);
} catch {
  return null;                        // caller renders "no profile"
}
```

Breaks on: a 500 from the profile service. The user sees "no profile"
instead of an error, and support cannot tell the two apart. Fix: catch
only `NotFoundError`; let the rest propagate.

## Rule 2. Boundaries and empty inputs

```ts
const latest = events.sort(byDate)[events.length - 1].at;
```

Breaks on: `events = []`. `undefined.at` throws. Also mutates the caller's
array (Rule 6). Fix: guard the empty case and sort a copy.

```ts
for (let page = 1; page <= Math.ceil(total / PAGE_SIZE); page++)
```

Breaks on: `total = 0`. `Math.ceil(0)` is `0`, the loop never runs, and
the "no results" branch below the loop is skipped because it checks
`page > 1`. Fix: handle `total === 0` before the loop.

```ts
const amountCents = Math.round(price * quantity * 100);
```

Breaks on: `price = 1.1, quantity = 3`. `1.1 * 3 = 3.3000000000000003`,
times 100 and rounded is `330`, fine; but `price = 0.07, quantity = 100`
gives `7.000000000000001` → `700`, while `price = 1.005, quantity = 1`
gives `100.49999999999999` → `100`, one cent short. Fix: hold prices in
cents as integers.

```ts
const isSameDay = a.toDateString() === b.toDateString();
```

Breaks on: `a` from the API in UTC, `b` from `new Date()` on a server in
`America/Los_Angeles`. `2026-10-16T02:00Z` and `2026-10-15T20:00-07:00`
are the same instant and different days. Fix: compare in one declared
zone.

## Rule 3. Null and undefined

```ts
const owner = users.find(u => u.id === doc.ownerId);
return owner.name;                    // or owner!.name
```

Breaks on: the owner was deleted. `Cannot read properties of undefined`.
Fix: handle the missing owner explicitly; decide what the caller sees.

```ts
const limit = options.limit || DEFAULT_LIMIT;
```

Breaks on: `options.limit = 0`, meaning "no rows", becomes the default.
Fix: `options.limit ?? DEFAULT_LIMIT`.

```ts
const company = await cache.get(companyId)?.company;
if (company.plan === 'enterprise') ...
```

Breaks on: cache miss. `company` is `undefined`, the optional chain hid
it, the next line throws. Fix: load on miss, or return early.

## Rule 4. Types that lie

```ts
const body = JSON.parse(raw) as CreateWorkerRequest;
await workers.create({ name: body.name.trim(), email: body.email });
```

Breaks on: `{"email": "a@b.c"}`. `name` is `undefined`, `.trim()` throws, a
400 becomes a 500. Fix: parse with the schema the repo uses for other
routes.

```ts
switch (status) {
  case 'queued': return 'Waiting';
  case 'running': return 'In progress';
  case 'done': return 'Finished';
}
```

Breaks on: `status = 'failed'`, added to the union last month. Returns
`undefined`; the UI shows a blank. Fix: `default: assertNever(status)`.

```ts
function findShift(id: string): Shift {
  return shifts.get(id) as Shift;
}
```

Breaks on: an id from a stale link. Returns `undefined` typed as `Shift`;
the crash lands three calls later in unrelated code. Fix: return
`Shift | undefined` and make callers decide.

## Rule 5. Async and concurrency

```ts
rows.forEach(async (row) => {
  await insert(row);
});
return { inserted: rows.length };
```

Breaks on: any `insert` failing. The function already returned success;
the rejection is unhandled. Fix: `await Promise.all(rows.map(insert))`, or
a sequential loop if order matters.

```ts
const invoice = await invoices.get(id);
if (invoice.chargedAt) return;
await stripe.charge(invoice);
await invoices.update(id, { chargedAt: now() });
```

Breaks on: two deliveries of the same webhook a few milliseconds apart.
Both read `chargedAt = null`, both charge. Fix: claim the row with a
conditional update before charging.

```ts
const [users, teams] = await Promise.all([loadUsers(), loadTeams()]);
```

Breaks on: `loadTeams` rejecting. The users result is discarded, the
whole page fails, even though teams are optional on this screen. Fix:
`allSettled`, and render what loaded. (The reverse is also a finding:
`allSettled` where a missing half must stop the operation.)

## Rule 6. Mutation and state

```ts
function latestFirst(items: Item[]) {
  return items.sort((a, b) => b.at - a.at);
}
```

Breaks on: the caller passing `state.items` from a store and rendering a
second list from it afterwards: that list is now reversed too. Fix:
`[...items].sort(...)` or `items.toSorted(...)`.

```ts
const DEFAULT_FILTERS = { tags: [] };
function withTag(filters = DEFAULT_FILTERS, tag: string) {
  filters.tags.push(tag);
  return filters;
}
```

Breaks on: the second call with no `filters` argument. It sees the first
call's tag. Fix: build a new object.

```ts
let cachedToken: string | undefined;
export async function getToken() {
  if (!cachedToken) cachedToken = await fetchToken();
  return cachedToken;
}
```

Breaks on: the token expiring; and on two concurrent first calls, which
both fetch. Fix: store the expiry with the token and dedupe the in-flight
promise.

## Rule 7. Existing callers and contracts

```ts
// before: function listWorkers(companyId: string): Promise<Worker[]>
// after:  function listWorkers(companyId: string, { activeOnly = true } = {})
```

Breaks on: `reports/headcount.ts` calling `listWorkers(id)` to count
everyone. It now undercounts. Fix: default to the old behaviour, or update
and name every caller in the finding.

```ts
// before: stored as { amount: number }   (cents)
// after:  stored as { amount: string }   (decimal)
```

Breaks on: any row written before the deploy. `parseDecimal(1250)` returns
`NaN`. Fix: read both shapes, or migrate first.

```ts
- expect(result.errors).toEqual(['email is required']);
+ expect(result.errors.length).toBeGreaterThan(0);
```

Breaks on: nothing yet, and that is the point: the test no longer proves
which error is returned. A weakened assertion to make a change pass is a
finding under Rule 7, with the assertion that should be restored.
