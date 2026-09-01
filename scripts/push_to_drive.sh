#!/usr/bin/env bash
# Pushes /pages and /assets/images to a Google Drive folder via rclone,
# authenticated as a service account (no browser/OAuth needed — this is
# what makes it usable from GitHub Actions). See docs/drive-cicd-setup.md
# for how to create the service account and share the folder with it.
#
# Required environment variables:
#   GDRIVE_SERVICE_ACCOUNT_JSON  - full contents of the service account key file
#   GDRIVE_FOLDER_ID             - target Drive folder's ID (from its URL)
set -euo pipefail
cd "$(dirname "$0")/.."

: "${GDRIVE_SERVICE_ACCOUNT_JSON:?Set GDRIVE_SERVICE_ACCOUNT_JSON to the full service account key JSON}"
: "${GDRIVE_FOLDER_ID:?Set GDRIVE_FOLDER_ID to the target Drive folder's ID}"

if ! command -v rclone >/dev/null; then
  echo "rclone not found on PATH — install it first (see docs/drive-cicd-setup.md)." >&2
  exit 1
fi

SA_FILE="$(mktemp)"
trap 'rm -f "$SA_FILE"' EXIT
printf '%s' "$GDRIVE_SERVICE_ACCOUNT_JSON" > "$SA_FILE"

export RCLONE_CONFIG_PTADRIVE_TYPE=drive
export RCLONE_CONFIG_PTADRIVE_SERVICE_ACCOUNT_FILE="$SA_FILE"
export RCLONE_CONFIG_PTADRIVE_ROOT_FOLDER_ID="$GDRIVE_FOLDER_ID"
export RCLONE_CONFIG_PTADRIVE_SCOPE=drive

echo "Syncing pages/ -> Drive:/pages ..."
rclone copy pages/ ptadrive:pages -v

echo "Syncing assets/images/ -> Drive:/images ..."
rclone copy assets/images/ ptadrive:images --exclude "*.md" -v

echo "Done — files are in the Drive folder. They inherit that folder's sharing settings automatically."
