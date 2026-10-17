# Examples per rule

Reject the left, accept the right. Each pair shows the finding's rewrite.

## Rule 1. Simple code

Reject: nested branches inside a loop, a boolean that switches behaviour.

```ts
function notify(users: User[], urgent: boolean) {
  for (const u of users) {
    if (u.email) {
      if (urgent) {
        if (!u.muted) sendSms(u.phone, URGENT_TEXT);
        sendEmail(u.email, URGENT_TEXT);
      } else if (!u.unsubscribed) {
        sendEmail(u.email, DIGEST_TEXT);
      }
    }
  }
}
```

Accept: two functions, one level deep, guards hoisted.

```ts
function sendUrgentNotice(users: User[]) {
  for (const user of users.filter(hasEmail)) {
    if (!user.muted) sendSms(user.phone, URGENT_TEXT);
    sendEmail(user.email, URGENT_TEXT);
  }
}

function sendDigest(users: User[]) {
  for (const user of users.filter(hasEmail)) {
    if (!user.unsubscribed) sendEmail(user.email, DIGEST_TEXT);
  }
}
```

Reject: a branch chain on a kind.

```ts
if (line.kind === 'labor') total += line.hours * line.rate;
else if (line.kind === 'material') total += line.quantity * line.unitCost;
else if (line.kind === 'fee') total += line.amount;
```

Accept: a lookup.

```ts
const LINE_AMOUNT: Record<LineKind, (line: InvoiceLine) => number> = {
  labor: (line) => line.hours * line.rate,
  material: (line) => line.quantity * line.unitCost,
  fee: (line) => line.amount,
};
total += LINE_AMOUNT[line.kind](line);
```

## Rule 2. Meaningful extractions

Reject: a cut, not an extraction. The helper carries the parent's locals
and hands back a bag of values; its name says nothing.

```ts
async function importApplicants(file: Buffer, companyId: string) {
  const { rows, errors, headerMap } = processFile(file, companyId);
  const { created, skipped } = handleRows(rows, headerMap, companyId, errors);
  return { created, skipped, errors };
}
```

Accept: each function has one purpose a domain expert would name, and the
call site reads without opening the helpers.

```ts
async function importApplicants(file: Buffer, companyId: string) {
  const sheet = parseApplicantSheet(file);
  const validRows = rejectRowsMissingRequiredFields(sheet.rows);
  const created = await createApplicants(validRows, companyId);
  return summariseImport(sheet, validRows, created);
}
```

Reject: a name that promises less than the body does.

```ts
function getSession(id: string) {
  const session = cache.get(id) ?? loadSession(id);
  cache.set(id, session);
  session.lastSeenAt = now();   // a getter that mutates
  return session;
}
```

Accept: the name says what happens, or the side effect moves out.

```ts
function touchSession(id: string) { ... }       // if the mutation is the point
// or
function getSession(id: string) { return cache.get(id) ?? loadSession(id); }
```

## Rule 3. Naming

| Reject | Accept | Why |
|---|---|---|
| `const data = await fetchRates()` | `const ratesByCurrency` | says what it holds and how it is keyed |
| `const delay = 500` | `const RETRY_DELAY_MS = 500` | unit and meaning |
| `if (flag)` | `if (isFirstRun)` | a boolean is a question |
| `function check(user)` | `function assertCanEdit(user)` | says it throws |
| `const TIMEOUT = 30` | `const SESSION_TTL_SECONDS = 30` | meaning and unit |
| `users.map(u => u.id)` | fine | one-line callback, scope matches |
| `for (const u of users) { ...20 lines... }` | `for (const user of users)` | the name lives past one line |
| `const res = await api.post(...)` | `const createdInvoice` | what it holds, not where it came from |
| `interface UserData` | `interface User` | name the concept |
| `let cnt = 0` | `let failedAttempts = 0` | abbreviation the repo does not use |
| `const list = workers.filter(isActive)` | `const activeWorkers` | plural noun that says the filter |

## Rule 4. Comments as a smell

Reject: the comment holds the name the code lacks.

```ts
// days until the document expires
const d = Math.ceil((doc.expiresAt - now) / DAY_MS);
```

Accept:

```ts
const daysUntilExpiry = Math.ceil((doc.expiresAt - now) / DAY_MS);
```

Reject: the comment holds the function the block should be.

```ts
// validate the request
if (!body.email || !isEmail(body.email)) throw new BadRequest('email');
if (!body.companyId) throw new BadRequest('companyId');
// build the applicant
const applicant = { ... };
```

Accept:

```ts
assertValidApplicantRequest(body);
const applicant = buildApplicant(body);
```

Reject: the comment explains a condition.

```ts
if (user.role === 'admin' || (user.id === doc.ownerId && !doc.locked)) { // can edit
```

Accept:

```ts
if (canEditDocument(user, doc)) {
```

Reject, blocking: the comment is now false.

```ts
// retries three times with backoff
await withRetry(fn, { attempts: 5 });
```

## Rule 5. Comments that earn their place

Accept: why, not what; short; at the line; names what it works around.

```ts
// Stripe sends `amount` in the smallest currency unit, and JPY has none,
// so dividing by 100 would be wrong for it. See docs/payments.md#zero-decimal.
const amount = ZERO_DECIMAL_CURRENCIES.has(currency) ? raw : raw / 100;
```

```ts
// The order matters: the index on (company_id, status) only serves this
// query when status is the second filter. Measured 40 ms vs 2.1 s on prod data.
```

```ts
// Node 20 `fetch` drops the body on a 303; follow it by hand.
// Remove when https://github.com/nodejs/undici/issues/1234 ships.
```

Reject: a why-comment on code that a rename would make obvious. That is a
Rule 4 finding, and the rename is the rewrite.

```ts
// we only want active workers here because inactive ones have no shifts
const list = workers.filter(w => w.status === 'active');
```

```ts
const workersWithShifts = workers.filter(isActive);
```
