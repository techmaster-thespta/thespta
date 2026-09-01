# One-Time Setup: GitHub → Google Drive

This is a **one-time setup** (or a re-do if credentials ever need rotating).
Once it's done, every push to `main` automatically builds the site, checks
it, and pushes the pages + images to a Google Drive folder — nobody needs
to run anything by hand.

You'll need: access to the **webmaster Gmail account**, and admin access to
the `techmaster-thespta/thespta` GitHub repo.

## 1. Create the Drive folder

1. In the webmaster Google account, go to [drive.google.com](https://drive.google.com).
2. Create a folder — e.g. **"PTA Website"**.
3. Right-click it → **Share** → **General access** → change to **Anyone with the link** → role **Viewer**.
4. Open the folder and copy its ID from the URL: `https://drive.google.com/drive/folders/`**`THIS_PART_IS_THE_ID`**.

Anything uploaded into this folder later (by the automation below) inherits
this same "anyone with the link" visibility automatically — you only set
this once, on the folder itself.

## 2. Create a Google Cloud service account

A service account is a robot Google account used only for automated
uploads — this is what lets GitHub Actions push files without a human
logging in every time.

1. Go to [console.cloud.google.com](https://console.cloud.google.com), signed in as the webmaster account.
2. Create a new project (or use an existing one) — e.g. "Thunder Hill PTA Site".
3. Go to **APIs & Services → Library**, search **Google Drive API**, click **Enable**.
4. Go to **APIs & Services → Credentials → Create Credentials → Service account**.
5. Give it a name (e.g. "pta-site-uploader"), click through the defaults, **Done**.
6. Click into the new service account → **Keys** tab → **Add Key → Create new key → JSON**. This downloads a `.json` file — **treat it like a password**. Don't commit it to the repo, don't email it around.
7. Copy the service account's email address (looks like `pta-site-uploader@your-project.iam.gserviceaccount.com`).

## 3. Share the Drive folder with the service account

1. Back in Drive, right-click the "PTA Website" folder → **Share**.
2. Paste in the service account's email (from step 2.7) → give it **Editor** access.

Without this step the service account can authenticate but has nowhere it's
allowed to upload to.

## 4. Add the secrets to GitHub

1. Go to `github.com/techmaster-thespta/thespta` → **Settings → Secrets and variables → Actions**.
2. **New repository secret** → name: `GDRIVE_FOLDER_ID` → value: the folder ID from step 1.4.
3. **New repository secret** → name: `GDRIVE_SERVICE_ACCOUNT_JSON` → value: open the `.json` file from step 2.6 in a text editor, copy its **entire contents**, paste as the secret value.

## 5. Test it

- **Settings → Actions → General** — confirm Actions are enabled for the repo.
- Push any small change (or go to the **Actions** tab → select the "Build, validate, and push to Drive" workflow → **Run workflow** to trigger it manually).
- Watch the run. The last step should say the files synced. Check the Drive folder — `pages/` and `images/` subfolders should appear with the site's files in them.

## What the workflow actually does, in order

1. Checks out the repo.
2. Runs `python3 src/build.py` — regenerates `/pages` from current `/config`.
3. Runs `python3 test/validate_build.py` — fails the whole run if anything's broken (unresolved config placeholder, malformed HTML).
4. If `/pages` changed, commits that back to the repo automatically (so what's in GitHub always matches what's live).
5. Installs `rclone` and runs `scripts/push_to_drive.sh`, authenticating as the service account — no browser, no stored personal login, works unattended in CI.

## If something breaks

| Symptom | Likely cause |
|---|---|
| Workflow fails at "Validate generated pages" | A real content bug — read the printed error, it names the exact file and problem |
| Workflow fails at "Push pages and images to Google Drive" | Check both secrets are set exactly right, and that the folder is actually shared with the service account's email (step 3) |
| Files show up in Drive but look broken/inaccessible when linked from Google Sites | Re-check step 1.3 — the *folder's* general access, not the individual file |
| Need to rotate credentials | Repeat steps 2.6–2.7 and 4.3 with a new key; you can then delete the old key from the service account's **Keys** tab |
