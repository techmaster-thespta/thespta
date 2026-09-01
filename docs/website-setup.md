# One-Time Setup: The Google Sites Website

This covers creating the actual Google Site and getting the 4 generated
pages live for the first time. For day-to-day content edits after this is
done, see `docs/SOP.md` instead.

## 1. Create the site

1. Go to [sites.google.com](https://sites.google.com), signed into the webmaster Google account.
2. **+ Blank** to start a new site.
3. Name it (top-left) — e.g. "Thunder Hill Elementary PTA".
4. Set the public site title (click the title text in the banner area).

## 2. Create the 4 pages

Use the **Pages** tab (right panel) → **Add page** for each:

| Page name | Becomes home page? |
|---|---|
| Home | Yes — Sites treats whichever page is first/root as home automatically, or set it explicitly in page settings |
| About | No |
| Get Involved | No |
| Events | No |

## 3. Paste each generated page

For each of the 4 pages:

1. Open `pages/<name>.html` (from this repo, or from the Drive `pages/` folder the CI workflow keeps in sync).
2. Select all, copy.
3. In Google Sites, go to that page → click where the content should go → **Insert → Embed → Embed code** → paste → **Insert**.

## 4. Preview and publish

1. Click the **eye icon** (top-right) to preview — check the mobile toggle inside it too.
2. Click **Publish** (top-right).
3. Set the site's URL path if prompted.

## 5. Fill in real page URLs

Once published, each page has a real URL (e.g.
`https://sites.google.com/view/thunderhillpta/events`). Every internal
button/footer link on the site currently points at `#` until you do this:

1. Open `config/site.json` → `page_urls`.
2. Replace each `"#"` with that page's real published URL.
3. Rebuild (`python3 src/build.py` or push to `main` and let CI do it).
4. Re-paste **all 4 pages** — every page's footer links to every other page.

## Ongoing updates

After this initial setup, you never repeat steps 1–2. Content changes go
through `config/*.json` (see `docs/SOP.md`), and re-publishing a changed
page is just: re-copy that one file's contents, paste over the existing
Embed block (click it → pencil icon → edit → replace → Update), Publish.
