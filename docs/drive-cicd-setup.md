# One-Time Setup: GitHub → Google Drive

This is a **one-time setup** (or a re-do if credentials ever need rotating).
Once it's done, every push to `main` automatically builds the site, checks
it, and pushes the pages + images to a Google Drive folder — nobody needs
to run anything by hand.

**Why this isn't a service account**: Google service accounts have *zero*
storage quota on a regular Gmail "My Drive" — uploads fail with
`storageQuotaExceeded` regardless of sharing permissions. That's only fixed
by a paid Google Workspace Shared Drive. Since this uses a plain Gmail
account (`techmaster.thespta@gmail.com`), we instead register our own small
OAuth app and authenticate it as that account directly — uploads then use
that account's own (effectively unlimited, personal) quota.

You'll need: access to `techmaster.thespta@gmail.com`, and admin access to
the `techmaster-thespta/thespta` GitHub repo.

## 1. Create the Drive folder

1. In that Google account, go to [drive.google.com](https://drive.google.com).
2. Create a folder — e.g. **"PTA Website"**.
3. Right-click it → **Share** → **General access** → change to **Anyone with the link** → role **Viewer**.
4. Open the folder and copy its ID from the URL: `https://drive.google.com/drive/folders/`**`THIS_PART_IS_THE_ID`**.

Anything uploaded into this folder later inherits this same "anyone with
the link" visibility automatically — you only set this once, on the folder
itself.

## 2. Create (or reuse) a Google Cloud project, and add an OAuth client

1. Go to [console.cloud.google.com](https://console.cloud.google.com), signed in as `techmaster.thespta@gmail.com`. Reuse an existing project if you made one already, or create a new one.
2. **APIs & Services → Library** → search **Google Drive API** → **Enable** (skip if already enabled).
3. **APIs & Services → OAuth consent screen**:
   - User type: **External**.
   - Fill in app name (e.g. "Thunder Hill PTA Site"), your support email, developer contact email.
   - **Scopes**: add `.../auth/drive.file` (narrow — this app can only touch files it creates itself, not your whole Drive).
   - Save through to the summary page.
   - **Publish the app** (button on the consent screen page) to move it from "Testing" to "In production". **This step matters** — apps left in "Testing" get refresh tokens that expire every 7 days, which would silently break the automation weekly.
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID**:
   - Application type: **Desktop app**.
   - Name it anything (e.g. "PTA site CI").
   - Create — this gives you a **Client ID** and **Client Secret**. Keep both handy for the next step.

## 3. Get a refresh token (one-time, interactive)

Run this **locally, not in CI** — it needs a real browser once:

```bash
export GDRIVE_CLIENT_ID="<from step 2>"
export GDRIVE_CLIENT_SECRET="<from step 2>"
pip install google-auth google-auth-oauthlib google-api-python-client
python3 scripts/push_to_drive.py --authorize
```

It prints a URL — open it, sign in as `techmaster.thespta@gmail.com`,
approve. The script then prints three values:

```
GDRIVE_CLIENT_ID     = ...
GDRIVE_CLIENT_SECRET = ...
GDRIVE_REFRESH_TOKEN = ...
```

## 4. Add the secrets to GitHub

`github.com/techmaster-thespta/thespta` → **Settings → Secrets and
variables → Actions → New repository secret**, one each for:

- `GDRIVE_CLIENT_ID`
- `GDRIVE_CLIENT_SECRET`
- `GDRIVE_REFRESH_TOKEN`
- `GDRIVE_FOLDER_ID` (from step 1.4)

## 5. Test it

- **Settings → Actions → General** — confirm Actions are enabled for the repo.
- Push any small change, or go to the **Actions** tab → "Build, validate, and push to Drive" → **Run workflow**.
- Check the Drive folder — `pages/` and `images/` subfolders should appear with the site's files in them.

## What the workflow actually does, in order

1. Checks out the repo.
2. Runs `python3 src/build.py` — regenerates `/pages` from current `/config`.
3. Runs `python3 test/validate_build.py` — fails the whole run if anything's broken.
4. If `/pages` changed, commits that back to the repo automatically.
5. Installs the Google API client libraries and runs `scripts/push_to_drive.py`, authenticating with the stored refresh token — no browser, no service account, works unattended in CI.

## If something breaks

| Symptom | Likely cause |
|---|---|
| Workflow fails at "Validate generated pages" | A real content bug — read the printed error, it names the exact file and problem |
| `storageQuotaExceeded` | Something got reverted to using a service account — this setup should never hit this error |
| `invalid_grant` / token errors | The refresh token expired or was revoked. Check the OAuth consent screen is still **"In production"**, not "Testing" (Step 2.3) — if it slipped back, or the token was revoked, redo Step 3 and update the `GDRIVE_REFRESH_TOKEN` secret |
| Files show up in Drive but look broken/inaccessible when linked from Google Sites | Re-check step 1.3 — the *folder's* general access, not individual files |
| Need to rotate credentials | Redo Step 3 to get a fresh refresh token; update the GitHub secret. The client ID/secret from Step 2 don't need to change unless you want a fresh OAuth client entirely |
