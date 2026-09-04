#!/usr/bin/env bash
# One-time install for the afterschool-flyer review's systemd --user
# timer. See docs/automation-service.md for what this service actually
# does and the bypassPermissions tradeoff it makes.
#
#   bash scripts/afterschool-review/install.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

mkdir -p "$UNIT_DIR"

# Symlinked, not copied: editing the unit files in the repo and
# re-running `systemctl --user daemon-reload` is then enough to update
# the running schedule, no re-install needed.
ln -sf "$SCRIPT_DIR/afterschool-review.service" "$UNIT_DIR/afterschool-review.service"
ln -sf "$SCRIPT_DIR/afterschool-review.timer" "$UNIT_DIR/afterschool-review.timer"

echo "Linked unit files into $UNIT_DIR"

if [ "$(loginctl show-user "$(whoami)" -p Linger --value 2>/dev/null)" != "yes" ]; then
  echo "Linger is not enabled for $(whoami) — the timer would stop firing whenever you're logged out."
  echo "Enabling it now (requires your account to allow this; may prompt for your password):"
  loginctl enable-linger "$(whoami)"
fi

systemctl --user daemon-reload
systemctl --user enable --now afterschool-review.timer

echo
echo "Installed and enabled. Next scheduled run:"
systemctl --user list-timers afterschool-review.timer --no-pager
echo
echo "Run it right now instead of waiting: systemctl --user start afterschool-review.service"
echo "Watch it run:                        journalctl --user -u afterschool-review.service -f"
echo "Uninstall:                           bash $SCRIPT_DIR/uninstall.sh"
