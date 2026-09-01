#!/usr/bin/env python3
"""
Pushes /pages and /assets/images to a Google Drive folder using the Drive
API directly — no rclone, no service account. See docs/drive-cicd-setup.md
for the full one-time setup.

Two modes:

  python3 scripts/push_to_drive.py --authorize
      One-time, interactive, run locally by a human (not in CI). Walks
      through Google's OAuth consent flow and prints a refresh token to
      save as a GitHub secret. Requires GDRIVE_CLIENT_ID and
      GDRIVE_CLIENT_SECRET to already be set as environment variables,
      from a "Desktop app" type OAuth client you created in Google Cloud
      Console (see docs/drive-cicd-setup.md).

  python3 scripts/push_to_drive.py
      Non-interactive (this is what CI runs). Requires GDRIVE_CLIENT_ID,
      GDRIVE_CLIENT_SECRET, GDRIVE_REFRESH_TOKEN, and GDRIVE_FOLDER_ID as
      environment variables. Uploads/updates pages/*.html into
      <folder>/pages and assets/images/* into <folder>/images.

Dependencies (NOT stdlib — installed via pip; see docs/drive-cicd-setup.md):
  google-auth google-auth-oauthlib google-api-python-client

Uses the narrow "drive.file" scope — this app can only see/manage files
it created itself, not your whole Drive.
"""
import argparse
import http.server
import mimetypes
import os
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
FOLDER_MIME = "application/vnd.google-apps.folder"


def require_env(name):
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(f"Missing required environment variable: {name}")
    return value


def authorize():
    from google_auth_oauthlib.flow import Flow

    client_id = require_env("GDRIVE_CLIENT_ID")
    client_secret = require_env("GDRIVE_CLIENT_SECRET")

    port = 53682
    redirect_uri = f"http://localhost:{port}/"
    flow = Flow.from_client_config(
        {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )
    auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")

    print("Open this URL in a browser and sign in as the account that should own the files:\n")
    print(auth_url)
    print(f"\nWaiting for approval (listening on {redirect_uri}) ...")

    code_holder = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            qs = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(qs)
            code_holder["code"] = params.get("code", [None])[0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body>Authorized \xe2\x80\x94 you can close this tab and return to the terminal.</body></html>")

        def log_message(self, *_args):
            pass

    server = http.server.HTTPServer(("localhost", port), Handler)
    server.handle_request()  # blocks until exactly one request arrives

    if not code_holder.get("code"):
        sys.exit("No authorization code received — did the approval fail or get cancelled?")

    flow.fetch_token(code=code_holder["code"])
    creds = flow.credentials

    print("\nSuccess. Save these as GitHub repo secrets (Settings → Secrets and variables → Actions):\n")
    print(f"  GDRIVE_CLIENT_ID     = {client_id}")
    print(f"  GDRIVE_CLIENT_SECRET = {client_secret}")
    print(f"  GDRIVE_REFRESH_TOKEN = {creds.refresh_token}")
    print("\n(GDRIVE_FOLDER_ID is separate — see docs/drive-cicd-setup.md.)")


def get_service():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials(
        token=None,
        refresh_token=require_env("GDRIVE_REFRESH_TOKEN"),
        client_id=require_env("GDRIVE_CLIENT_ID"),
        client_secret=require_env("GDRIVE_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    return build("drive", "v3", credentials=creds)


def find_or_create_subfolder(service, parent_id, name):
    query = (
        f"'{parent_id}' in parents and name = '{name}' "
        f"and mimeType = '{FOLDER_MIME}' and trashed = false"
    )
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]
    folder = service.files().create(
        body={"name": name, "mimeType": FOLDER_MIME, "parents": [parent_id]},
        fields="id",
    ).execute()
    return folder["id"]


def upload_file(service, folder_id, path: Path):
    from googleapiclient.http import MediaFileUpload

    mime_type, _ = mimetypes.guess_type(str(path))
    mime_type = mime_type or "application/octet-stream"
    media = MediaFileUpload(str(path), mimetype=mime_type, resumable=False)

    query = f"'{folder_id}' in parents and name = '{path.name}' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    existing = results.get("files", [])

    if existing:
        service.files().update(fileId=existing[0]["id"], media_body=media).execute()
        print(f"  updated {path.name}")
    else:
        service.files().create(
            body={"name": path.name, "parents": [folder_id]}, media_body=media
        ).execute()
        print(f"  created {path.name}")


def push():
    folder_id = require_env("GDRIVE_FOLDER_ID")
    service = get_service()

    pages_dir = ROOT / "pages"
    images_dir = ROOT / "assets" / "images"

    if pages_dir.is_dir():
        pages_folder_id = find_or_create_subfolder(service, folder_id, "pages")
        print("Syncing pages/ ...")
        for f in sorted(pages_dir.glob("*.html")):
            upload_file(service, pages_folder_id, f)

    if images_dir.is_dir():
        images_folder_id = find_or_create_subfolder(service, folder_id, "images")
        print("Syncing assets/images/ ...")
        for f in sorted(images_dir.iterdir()):
            if f.is_file() and f.suffix.lower() != ".md":
                upload_file(service, images_folder_id, f)

    print("\nDone — files are in the Drive folder. They inherit that folder's sharing settings automatically.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorize", action="store_true", help="One-time interactive setup to obtain a refresh token")
    args = parser.parse_args()

    if args.authorize:
        authorize()
    else:
        push()


if __name__ == "__main__":
    main()
