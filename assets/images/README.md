Source images for the site. GitHub Actions copies these into the deployed
GitHub Pages site's `images/` folder on every push to `main` — no external
hosting, no sharing settings to manage.

Drop a new image in here, then point `config/site.json`'s
`hero_image_filename` or `page_header_image_filename` at its filename (see
`docs/SOP.md` Task 6). The generated pages reference it as a relative
`images/<file>` URL, which resolves correctly once deployed.
