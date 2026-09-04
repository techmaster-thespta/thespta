#!/usr/bin/env bash
# Runs the review-afterschool-flyers skill headlessly via the `claude`
# CLI — see docs/automation-service.md for what this does and why, and
# for the one-time systemd install steps. All the actual task logic
# lives in .claude/skills/review-afterschool-flyers/SKILL.md, not here
# or in a separate prompt file, so it stays the one source of truth
# whether it's run by this automation, or a human asks Claude Code to
# "review the afterschool flyers" interactively.
#
# Invoked by the afterschool-review.timer/.service unit files in this
# same directory; safe to run by hand too:
#
#   bash scripts/afterschool-review/run.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/thespta-afterschool-review"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$(date +%Y%m%d-%H%M%S).log"

cd "$REPO_DIR"

# bypassPermissions is required here, not just convenient: this runs
# with no TTY and no human present, so any permission prompt (a normal
# tool call would otherwise trigger) would hang forever waiting for
# input that can never come. The safety boundary for this job is the
# narrow, version-controlled, human-reviewed skill content itself
# (.claude/skills/review-afterschool-flyers/SKILL.md), not runtime
# permission gating.
claude -p "/review-afterschool-flyers" \
  --permission-mode bypassPermissions \
  --output-format text \
  > "$LOG_FILE" 2>&1

echo "afterschool-review: log written to $LOG_FILE"
