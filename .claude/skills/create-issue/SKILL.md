---
name: create-issue
description: Collaboratively plan a change with the user in conversation, then file a well-scoped GitHub issue for it. Use "gh" for all GitHub operations.
---

# Plan a change with the user, then file it as an issue

Invoked as `/create-issue` (optionally with an initial description as
args). This is a **planning conversation first, issue creation second** —
don't file anything until the user has confirmed the scope.

## Steps

1. **Get the idea.** If `args` already contains a description, start from
   that; otherwise ask what they want.

2. **Clarify collaboratively.** Ask about whatever's genuinely ambiguous —
   don't interrogate over things a reasonable default answers. Things
   worth pinning down:
   - Is this actually a **config-only** change (a new event/sponsor/board
     member/flyer, a text/color/link edit) or does it need new
     **structural** work (new section type, new page, layout change)?
     This determines which skill `from-issue` will later route through.
   - Exact content: real names/dates/links, not placeholders — an issue
     that says "add our new sponsor" without the sponsor's name and URL
     isn't implementable later without re-asking.
   - For structural asks: which page(s) it affects, and roughly what it
     should look like (reuse an existing pattern from `.claude/CLAUDE.md`
     — cards/grid, icon circles, etc. — where possible, rather than
     inventing a new visual pattern).

3. **Draft the issue** and show it to the user before creating anything:

   ```markdown
   ## Summary
   <1-2 sentences>

   ## Details
   <the specifics agreed on in conversation — exact text/data/links/pages>

   ## Scope: config-only
   <or: Scope: structural — plus which src/templates files are likely involved>

   ## Acceptance criteria
   - [ ] <concrete, checkable outcome>
   - [ ] python3 test/validate_build.py passes
   ```

   The `Scope:` line is load-bearing — `from-issue` reads it to decide
   whether it can proceed autonomously (config-only) or should treat the
   issue text itself as explicit sign-off for a `src/` change (structural).

4. **Confirm** with the user — this is the one point to actually pause and
   ask "does this look right to file?" rather than assuming. Adjust if not.

5. **File it.**
   ```
   gh issue create --title "<short, specific title>" --body "<the confirmed draft>"
   ```

6. **Report back** the issue number and URL. Mention that `/from-issue
   <number>` is how it gets implemented later (by this session or a fresh
   one — the issue is self-contained).

## Do not

- Do not run `gh issue create` before the user has seen and confirmed the drafted body.
- Do not start implementing anything in this skill — that's `from-issue`'s job, deliberately kept separate so planning and execution don't get rushed together.
- Do not invent scope the user didn't actually ask for while "improving" the draft.
