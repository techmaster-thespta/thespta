# One-Time Setup: GitHub Pages

This is a **one-time repo setting**. Once it's on, every push to `main`
automatically builds the site, checks it, and publishes it live at
`https://techmaster-thespta.github.io/thespta/` — no images to host
separately, no credentials, no service accounts, no OAuth tokens.

## 1. Turn on GitHub Pages for this repo

1. `github.com/techmaster-thespta/thespta` → **Settings → Pages**.
2. Under **Build and deployment → Source**, choose **GitHub Actions** (not "Deploy from a branch" — the workflow handles building and deploying itself).
3. That's it. No branch to create, nothing else to configure here.

## 2. Confirm it's live

- Push anything to `main`, or go to **Actions** tab → "Build, validate, and deploy to GitHub Pages" → **Run workflow**.
- Once green, visit `https://techmaster-thespta.github.io/thespta/home.html` — it should show the live Home page.
- Each page is at its own URL: `.../home.html`, `.../about.html`, `.../get-involved.html`, `.../events.html`.

## 3. Wire each page into Google Sites (one time, per page)

Instead of pasting HTML into an Embed-code box, embed the **live URL** —
this means future content changes need zero re-pasting; the embed just
always shows whatever's currently live.

1. In the Google Sites editor, go to the matching page (Home, About, Get Involved, Events).
2. Click where the content should go → **Insert → Embed → By URL**.
3. Paste the matching URL from Step 2, e.g. `https://techmaster-thespta.github.io/thespta/home.html`.
4. Click **Insert**, then **Publish**.

Do this once per page. After that, every content change (an event, a
board member, a color) just needs a config edit + push — GitHub Actions
rebuilds and redeploys automatically, and the Google Sites embed picks it
up with no further action there.

## What the workflow actually does, in order

1. Checks out the repo.
2. Runs `python3 src/build.py` — regenerates `/pages` from current `/config`.
3. Runs `python3 test/validate_build.py` — fails the whole run if anything's broken.
4. If `/pages` changed, commits that back to the repo automatically.
5. Assembles a `site/` folder: the 4 generated HTML files plus `assets/images/*` copied into `site/images/`.
6. Uploads and deploys that folder as the live GitHub Pages site.

## If something breaks

| Symptom | Likely cause |
|---|---|
| Workflow fails at "Validate generated pages" | A real content bug — read the printed error, it names the exact file and problem |
| Workflow fails at "Deploy to GitHub Pages" | Pages isn't turned on for the repo yet — redo Step 1 |
| Live site loads but images are broken | Check `assets/images/` actually contains the filenames referenced in `config/site.json` (`hero_image_filename`, `page_header_image_filename`) |
| Google Sites embed shows stale content | The embed is "By URL," which should always be live — try removing and re-adding the embed block if it seems cached |
| Need to change the site's Pages URL (e.g. a custom domain) | Settings → Pages → add a custom domain, then update every `page_urls.*` entry in `config/site.json` to match and rebuild |
| Workflow is green but the live URL 404s ("Page not found · GitHub Pages") | Pages' **source** setting can silently stay on legacy branch-deploy mode even after `actions/deploy-pages` reports success — check with `gh api repos/techmaster-thespta/thespta/pages` and look for `"build_type"`. If it says `"legacy"` instead of `"workflow"`, fix it with `gh api -X PUT repos/techmaster-thespta/thespta/pages -f build_type=workflow`, then re-run the workflow. Don't trust a green checkmark alone here — verify with `curl` against the actual live URL. |
