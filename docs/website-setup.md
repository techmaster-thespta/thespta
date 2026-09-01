# One-Time Setup: The Google Sites Website

This covers creating the actual Google Site and wiring its 4 pages to the
live GitHub Pages site. Do `docs/github-pages-setup.md` first — this
depends on that URL already being live. For day-to-day content edits after
both are done, see `docs/SOP.md` instead.

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

## 3. Embed each page by URL

Unlike a copy-pasted code block, this stays live forever — no re-pasting
needed after future content changes.

For each of the 4 pages, in Google Sites:

1. Go to that page → click where the content should go.
2. **Insert → Embed → By URL**.
3. Paste the matching GitHub Pages URL:

   | Google Sites page | Embed this URL |
   |---|---|
   | Home | `https://techmaster-thespta.github.io/thespta/home.html` |
   | About | `https://techmaster-thespta.github.io/thespta/about.html` |
   | Get Involved | `https://techmaster-thespta.github.io/thespta/get-involved.html` |
   | Events | `https://techmaster-thespta.github.io/thespta/events.html` |

4. Click **Insert**.

## Two different URLs, two different jobs

It's easy to conflate these, so to be explicit:

- **GitHub Pages URLs** (`https://techmaster-thespta.github.io/thespta/*.html`)
  are the embed *source* — what you paste into "Embed → By URL" in step 3
  above. This is where the actual HTML content lives.
- **Google Sites sub-page URLs** (`https://sites.google.com/view/<site>/<slug>`)
  are what every link *inside* the generated pages points to (nav cards,
  "View Events →", "Get Involved →", etc.), via `google_sites_base_url` +
  `page_urls.*` in `config/site.json`. This keeps a visitor who clicks a
  link inside Google Sites' own nav/header/footer shell, instead of
  dropping them onto a bare embedded page with no way back.

The convention that makes this work: **each Google Sites sub-page's name is
identical to its generated HTML file's name, minus `.html`** (`home`,
`about`, `get-involved`, `events`). `page_urls.*` in `config/site.json`
just holds that slug — `build.py` turns it into a full URL by prefixing
`google_sites_base_url`.

## Adding a new page later

1. Add the new page to this Google Site (**Pages** tab → **Add page**),
   named to match the slug you're about to use — e.g. a page named
   `fundraising` for a URL of `.../view/<site>/fundraising`.
2. Add a matching template under `src/templates/pages/` (see
   `.claude/CLAUDE.md` → "Adding a new modular content type" if it needs a
   new content type too) and a `page_urls.fundraising` entry in
   `config/site.json` set to `"fundraising"`.
3. Rebuild and push (Task 7 in `docs/SOP.md`).
4. Embed the new page **by URL** in Google Sites, same as step 3 above,
   pointing at `https://techmaster-thespta.github.io/thespta/fundraising.html`.

As long as the Google Sites page name and the `page_urls` slug match, every
existing page's nav/links to the new page work automatically — nothing
else to wire up.

## 4. Preview and publish

1. Click the **eye icon** (top-right) to preview — check the mobile toggle inside it too.
2. Click **Publish** (top-right).
3. Set the site's URL path if prompted.

## Ongoing updates

After this, you never repeat any of the above. Content changes go through
`config/*.json` (see `docs/SOP.md`) — push to `main`, GitHub Actions
rebuilds and redeploys to GitHub Pages automatically, and every embedded
page picks up the change immediately since it's a live URL, not a static
paste. Nothing to touch in Google Sites again unless you're adding a
brand-new page.
