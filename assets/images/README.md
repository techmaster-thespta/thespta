Source images kept in the repo for backup/version history and pushed to
the shared Google Drive folder by CI on every push to `main` (see
`docs/drive-cicd-setup.md`).

These are **not** embedded directly into the generated pages — Google
Sites pages reference them by Drive link instead (kept small in the HTML,
easy to swap). To change which image shows where, see `docs/SOP.md` Task 6
— it's a `config/site.json` edit (`hero_image_drive_id` /
`page_header_image_drive_id`), not a file-naming convention here.
