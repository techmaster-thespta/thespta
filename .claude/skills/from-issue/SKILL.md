---
name: from-issue
description: Pull a GitHub issue by number, implement what it describes, and open a PR. Use "gh" for all GitHub operations.
---

# Implement a GitHub issue and open a PR

Invoked as `/from-issue <issue-number>`. Takes an issue number, reads it,
implements the change, and opens a PR — end to end, no other input needed
unless the issue is genuinely unclear (see "If the issue is unclear" below).

## Steps

1. **Read the issue.**
   ```
   gh issue view <issue-number> --json number,title,body,labels,state
   ```
   If it's already closed, stop and tell the user rather than reopening work silently.

2. **Classify the scope** from the issue body. Look for the "Scope:" line
   the `create-issue` skill adds (`Scope: config-only` or `Scope:
   structural`). If it's missing (a hand-written issue), classify it
   yourself:
   - **Config-only** — adding/editing/removing an event, board member,
     sponsor, or flyer; changing site info, colors, fonts, or a Drive
     image ID. Route through the matching existing skill's exact file/field
     knowledge (`.claude/skills/add-event/`, `add-board-member/`,
     `add-sponsor/`, `add-flyer/`) rather than re-deriving it — those
     skills already document the precise JSON shape expected.
   - **Structural** — anything touching `src/templates/` or `src/build.py`
     (new page, new section type, layout change, new modular content
     type). The issue text is the user's explicit authorization for this
     specific change — per `.claude/CLAUDE.md` you'd normally ask before
     touching `src/`, but a filed issue requesting it already *is* that
     ask. Still keep the change scoped to exactly what the issue
     describes, not a broader refactor.

3. **Branch.**
   ```
   git checkout -b issue-<issue-number>-<short-slug>
   ```

4. **Implement.** Make the change. If config-only, follow the relevant
   skill's file/steps exactly. If structural, follow the "Adding a new
   modular content type" pattern in `.claude/CLAUDE.md` when applicable.

5. **Build and validate — this gates everything after it.**
   ```
   python3 src/build.py
   python3 test/validate_build.py
   ```
   If either fails: **do not commit, push, or open a PR.** Instead, comment
   on the issue explaining what failed and why (`gh issue comment
   <issue-number> --body "..."`), leave the branch as-is locally, and stop.

6. **Commit.**
   ```
   git add -A
   git commit -m "<concise summary>

   Closes #<issue-number>"
   ```

7. **Push and open the PR.**
   ```
   git push -u origin issue-<issue-number>-<short-slug>
   gh pr create --title "<title>" --body "Closes #<issue-number>

   <2-3 sentence summary of what changed and why>

   ## Test plan
   - [x] python3 src/build.py — no unresolved placeholders
   - [x] python3 test/validate_build.py — passed
   - [ ] Confirm the live GitHub Pages URL reflects the change once merged"
   ```

8. **Report back**: the PR URL, which live page(s) will update once merged
   and GitHub Actions redeploys (per `docs/SOP.md` Task 7 — no manual
   Google Sites step needed either way), and confirm the branch — never
   merge the PR yourself.

## If the issue is unclear

Don't guess at scope-defining details (e.g. "add a sponsor section" but no
actual sponsor name/link given, or a structural request vague enough that
two reasonable implementations diverge). Instead:

```
gh issue comment <issue-number> --body "<specific question(s)>"
```

and stop — do not create a branch or implement anything speculative. Tell
the user you've asked for clarification on the issue rather than guessing.

## Do not

- Do not push directly to `main`. Always a branch + PR.
- Do not merge the PR.
- Do not force-push.
- Do not implement more than the issue asks for, even if you notice other improvements while in there — file a new issue for those instead (or mention them in the PR description as a suggestion, unimplemented).
