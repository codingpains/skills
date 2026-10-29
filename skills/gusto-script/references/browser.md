# Images from sites that block `media.py`

Big retail sites and stock libraries answer `media.py` with 403, and some
pages load their images with JavaScript, so `page` finds none. A real
browser gets through both. In T3 Code, the preview browser does it, and
its downloads land on disk untouched, without passing through the chat.

Use it only for originals `media.py` can't reach. The rules don't change:
the image must match the script, it stays a private reference, and it is
recorded in `sources.json`.

The T3 tools are deferred: load `preview_open`, `preview_evaluate`,
`preview_status` and `t3_preview_close` with ToolSearch first. Without
them (not a T3 session), search for the garment on another site instead.

## 1. Open the page in the background

`preview_open` with the page URL, `open: false` and
`reuseExistingTab: false`. Keep the `tabId` it returns and pass it to
every call. If the first `preview_evaluate` fails with "navigated or
closed", the site ran a bot check and reloaded; run it again.

## 2. List the images

`preview_evaluate` with:

```js
(async () => {
  for (let y = 0; y < document.body.scrollHeight; y += 800) {
    window.scrollTo(0, y);
    await new Promise(r => setTimeout(r, 250));
  }
  await new Promise(r => setTimeout(r, 1500));
  return [...document.images]
    .filter(i => i.naturalWidth >= 150)
    .map(i => ({ src: i.currentSrc || i.src, w: i.naturalWidth, alt: i.alt.slice(0, 90) }));
})()
```

Product grids show small thumbnails, so the width says little. Many
retail image URLs carry their size (`w560_q80`, `260nw`), and a larger
size in the same URL often works, e.g. `w2000_q80`. Otherwise open the
product page and list again.

## 3. Download one

`preview_evaluate`, with the image URL and a file name:

```js
(async () => {
  const r = await fetch("<image URL>");
  const blob = await r.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "<frame>-<what>";
  document.body.appendChild(a);
  a.click();
  a.remove();
  return { status: r.status, type: blob.type, bytes: blob.size };
})()
```

A status other than 200, or a tiny size, means it didn't work: try the
URL `page` listed at its own size, or another image.

## 4. Import it, before closing the tab

T3 deletes a tab's downloads when the tab closes. `preview_status` with
the `tabId` lists `downloads`, each with its `fileName` and `path`. Copy
it into the production right away:

```
media.py import <path> --image-url <image URL> --page <page URL> --out <production>/refs --name <frame>-<what>
```

`import` names the file by its real type and records it in
`sources.json` with `"via": "browser"`. Then Read it, as with any
original.

## 5. Close the tab

`t3_preview_close` with the `tabId`, once every original from that site
is imported.

Stock libraries show only small watermarked previews without a licence.
They do as a private reference, but editorial and retail photos show the
garment better.
