#!/usr/bin/env bash
# Removes the afterschool-flyer review's systemd --user timer. This only
# removes the schedule — the skill, the script, and the unit file
# templates all stay in the repo either way, so re-installing later is
# just install.sh again.
#
#   bash scripts/afterschool-review/uninstall.sh
set -euo pipefail

UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

systemctl --user disable --now afterschool-review.timer 2>/dev/null || true
rm -f "$UNIT_DIR/afterschool-review.service" "$UNIT_DIR/afterschool-review.timer"
systemctl --user daemon-reload

echo "Uninstalled — the timer no longer runs. Linger was left as-is (in case other user services need it)."
