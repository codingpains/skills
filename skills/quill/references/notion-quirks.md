# Notion API quirks — read before any batch write

Loaded by the **Story Agent** in `catalogue` mode before it commits a
batch of rows. These quirks have bitten the story-cataloguing work enough
times to be worth a dedicated reference.

## 1. Timeouts don't mean the write failed

The Notion API times out intermittently. The single worst trap:

- A timeout does **not** mean the call failed. Many writes succeed on the
  backend *after* the API call times out on your end.
- A blind retry on a timed-out create often **duplicates** the row.

**Workaround — idempotent commit.** Before (re)creating any story:

1. Query the DB for a row whose `Story ID` equals the ID you're about to
   write (or, if the ID isn't assigned yet, whose `Story` title matches).
2. If it already exists, treat that story as committed — do not re-create
   it. Record its URL and move on.
3. Only create when the lookup returns nothing.

Write in **small batches (5–8 rows per pass)** and re-query between
passes so a mid-batch timeout can resume cleanly instead of duplicating.

## 2. Allocate IDs against the live DB, not a cached counter

`Story ID` is the source of truth for numbering — there is no external
counter anymore. Before a batch, query `MAX(Story ID)` (parse the numeric
suffix, since it's stored as text) and allocate sequentially from there.
If a timeout forces a resume, **re-query the max** rather than trusting an
in-memory number — a partially-committed batch may have advanced it.

## 3. Adding an Epic select option

`Epic` is a fixed `select`. Writing a story into a new epic (e.g.
"Versioning") requires adding the option to the property **first**, via
`notion-update-data-source` on the data source. This is a schema change —
the command gates it with the user before doing it. Use the exact display
name the user confirmed; the option is then usable on row creation.

## 4. Notion's markdown parser splits inline links

When you write `[**ID** — title](url)`, Notion's parser may split it into
two adjacent links sharing the same URL. This matters if you later
search-and-replace against the stored text. If you must reconcile stored
content, `fetch` the page and craft your match against what's actually
stored, not what you wrote. For catalogue mode this mostly means: keep
plain-text `XXX-USR-NNN` cross-references out of link syntax (see
`story-conventions.md`).

## 5. Verify, don't assume

After a batch, query the DB for the IDs you intended to write and confirm
each exists exactly once. Report any that are missing or duplicated rather
than silently assuming success.
