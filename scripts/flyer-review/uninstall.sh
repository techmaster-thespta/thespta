#!/usr/bin/env bash
# Removes the flyer review's systemd --user timer. This only removes
# the schedule — the skills, the scripts, and the unit file templates
# all stay in the repo either way, so re-installing later is just
# install.sh again.
#
#   bash scripts/flyer-review/uninstall.sh
set -euo pipefail

UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

systemctl --user disable --now flyer-review.timer 2>/dev/null || true
rm -f "$UNIT_DIR/flyer-review.service" "$UNIT_DIR/flyer-review.timer"
systemctl --user daemon-reload

echo "Uninstalled — the timer no longer runs. Linger was left as-is (in case other user services need it)."
