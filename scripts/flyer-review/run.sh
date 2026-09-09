#!/usr/bin/env bash
# Runs every flyer-review skill headlessly via the `claude` CLI, one
# after another in a single scheduled run — see
# docs/automation-service.md for what this does and why, and for the
# one-time systemd install steps.
#
# This replaced a previous setup with one systemd timer per content
# type (scripts/afterschool-review/, now removed): each flyer type's
# actual review logic is genuinely different (different config schemas,
# fundraisers need reprint-vs-new-campaign judgment, PTA meetings need
# to never guess a date) so each kept its own skill file — but the
# systemd plumbing around them (timer, service, install/uninstall) was
# identical boilerplate, so that layer is merged into this one script
# instead of copy-pasted per content type. A fourth flyer-backed content
# type means one more `run_skill` line below, not a whole new
# service/timer/install.sh trio — already proven twice (fundraisers,
# then PTA meetings).
#
# All the actual task logic for each skill lives in its own
# .claude/skills/<name>/SKILL.md, not here or in a separate prompt
# file, so each stays the one source of truth whether it's run by this
# automation, or a human asks Claude Code to run it interactively.
#
# Invoked by the flyer-review.timer/.service unit files in this same
# directory; safe to run by hand too:
#
#   bash scripts/flyer-review/run.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/thespta-flyer-review"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$(date +%Y%m%d-%H%M%S).log"

cd "$REPO_DIR"

run_skill() {
  local skill="$1"
  echo "===== /$skill =====" >> "$LOG_FILE"
  # bypassPermissions is required here, not just convenient: this runs
  # with no TTY and no human present, so any permission prompt (a
  # normal tool call would otherwise trigger) would hang forever
  # waiting for input that can never come. The safety boundary for this
  # job is the narrow, version-controlled, human-reviewed skill content
  # itself (.claude/skills/<name>/SKILL.md), not runtime permission
  # gating.
  claude -p "/$skill" \
    --permission-mode bypassPermissions \
    --output-format text \
    >> "$LOG_FILE" 2>&1
}

run_skill "review-afterschool-flyers"
run_skill "review-fundraiser-flyers"
run_skill "review-pta-meeting-flyers"

echo "flyer-review: log written to $LOG_FILE"
