#!/usr/bin/env bash
# One-time install for the flyer review's systemd --user timer (covers
# both afterschool-program and fundraiser flyers — see run.sh). See
# docs/automation-service.md for what this service actually does and
# the bypassPermissions tradeoff it makes.
#
# If you previously installed the old, afterschool-only
# "afterschool-review" service, uninstall it first:
#
#   bash scripts/afterschool-review/uninstall.sh   # if that directory still exists locally
#   # or, if it's already gone:
#   systemctl --user disable --now afterschool-review.timer
#   rm -f ~/.config/systemd/user/afterschool-review.service ~/.config/systemd/user/afterschool-review.timer
#   systemctl --user daemon-reload
#
# Then install this one:
#
#   bash scripts/flyer-review/install.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

mkdir -p "$UNIT_DIR"

# Symlinked, not copied: editing the unit files in the repo and
# re-running `systemctl --user daemon-reload` is then enough to update
# the running schedule, no re-install needed.
ln -sf "$SCRIPT_DIR/flyer-review.service" "$UNIT_DIR/flyer-review.service"
ln -sf "$SCRIPT_DIR/flyer-review.timer" "$UNIT_DIR/flyer-review.timer"

echo "Linked unit files into $UNIT_DIR"

if [ "$(loginctl show-user "$(whoami)" -p Linger --value 2>/dev/null)" != "yes" ]; then
  echo "Linger is not enabled for $(whoami) — the timer would stop firing whenever you're logged out."
  echo "Enabling it now (requires your account to allow this; may prompt for your password):"
  loginctl enable-linger "$(whoami)"
fi

systemctl --user daemon-reload
systemctl --user enable --now flyer-review.timer

echo
echo "Installed and enabled. Next scheduled run:"
systemctl --user list-timers flyer-review.timer --no-pager
echo
echo "Run it right now instead of waiting: systemctl --user start flyer-review.service"
echo "Watch it run:                        journalctl --user -u flyer-review.service -f"
echo "Uninstall:                           bash $SCRIPT_DIR/uninstall.sh"
