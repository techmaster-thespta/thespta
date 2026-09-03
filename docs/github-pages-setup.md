# One-Time Setup: GitHub Pages + Custom Domain

This is a **one-time repo setting**. Once it's on, every push to `main`
automatically builds the site, checks it, and publishes it live at
`https://techmaster-thespta.github.io/thespta/` and the custom domain
below — no images to host separately, no credentials, no service
accounts, no OAuth tokens, and (since the migration off Google Sites)
nothing to re-embed anywhere.

## 1. Turn on GitHub Pages for this repo

1. `github.com/techmaster-thespta/thespta` → **Settings → Pages**.
2. Under **Build and deployment → Source**, choose **GitHub Actions** (not "Deploy from a branch" — the workflow handles building and deploying itself).
3. That's it. No branch to create, nothing else to configure here.

## 2. Confirm it's live

- Push anything to `main`, or go to **Actions** tab → "Build, validate, and deploy to GitHub Pages" → **Run workflow**.
- Once green, visit `https://techmaster-thespta.github.io/thespta/home.html` — it should show the live Home page.
- Each page is at its own URL: `.../home.html`, `.../about.html`, `.../get-involved.html`, `.../events.html`, `.../newsletter.html`.

## 3. Point the custom domain at GitHub Pages

The site is meant to be reached at `config/site.json`'s `custom_domain`
value (currently `www.thespta.org`), not the raw `*.github.io` URL.
`src/build.py` already generates a `CNAME` file from that config value on
every build, and the deploy workflow includes it in what gets published
— the repo side of this is automatic. What's left is entirely outside
this repo:

1. **DNS**: at whatever registrar/DNS provider manages `thespta.org`,
   add or update a `CNAME` record for the `www` subdomain, pointing it at
   `techmaster-thespta.github.io` (no `https://`, no trailing slash —
   just the hostname). If this domain previously pointed at Google Sites,
   this replaces that record — a domain can only point at one host's DNS
   at a time.
2. **GitHub**: `Settings → Pages → Custom domain` → enter
   `www.thespta.org` → Save. GitHub checks the DNS record matches, then
   automatically provisions a Let's Encrypt HTTPS certificate — this can
   take anywhere from a few minutes to about 24 hours after DNS
   propagates. Once the "Enforce HTTPS" checkbox becomes available,
   check it.
3. **Verify**: once the cert is issued, `https://www.thespta.org/home.html`
   should serve the live site directly (no more Google Sites in the
   chain at all).

**If this domain was previously connected to a Google Site**: detach it
there too (Google Sites → that site → **Settings → Custom URLs** → remove
it) once DNS points at GitHub Pages instead — otherwise Google Sites will
keep showing a "domain not verified" or similar state for a domain it can
no longer actually serve. The Google Site itself can stay published or be
unpublished; that's a separate decision from the domain, and nothing in
this repo depends on it either way.

## What the workflow actually does, in order

1. Checks out the repo.
2. Syncs events from the shared Google Calendar (`scripts/sync_calendar_events.py`).
3. Runs `python3 src/build.py` — regenerates `/pages` (including `pages/CNAME`) from current `/config`.
4. Runs `python3 test/validate_build.py` — fails the whole run if anything's broken.
5. If `/pages` or `config/events.json` changed, commits that back to the repo automatically.
6. Assembles a `site/` folder: the generated HTML files, `CNAME`, and `assets/images/*` copied into `site/images/`.
7. Uploads and deploys that folder as the live GitHub Pages site.

## If something breaks

| Symptom | Likely cause |
|---|---|
| Workflow fails at "Validate generated pages" | A real content bug — read the printed error, it names the exact file and problem |
| Workflow fails at "Deploy to GitHub Pages" | Pages isn't turned on for the repo yet — redo Step 1 |
| Live site loads but images are broken | Check `assets/images/` actually contains the filenames referenced in `config/site.json` (`hero_image_filename`, `page_header_image_filename`) |
| Custom domain shows a GitHub "domain not verified" or SSL warning | DNS hasn't propagated yet, or the `www` CNAME record doesn't point at `techmaster-thespta.github.io` — double-check Step 3 above; propagation can take a while |
| `www.thespta.org` loads something unrelated / still shows the old Google Site | DNS is still pointed at Google's hosting — Step 3's DNS change hasn't been made or hasn't propagated yet |
| Workflow is green but the live URL 404s ("Page not found · GitHub Pages") | Pages' **source** setting can silently stay on legacy branch-deploy mode even after `actions/deploy-pages` reports success — check with `gh api repos/techmaster-thespta/thespta/pages` and look for `"build_type"`. If it says `"legacy"` instead of `"workflow"`, fix it with `gh api -X PUT repos/techmaster-thespta/thespta/pages -f build_type=workflow`, then re-run the workflow. Don't trust a green checkmark alone here — verify with `curl` against the actual live URL. |
