---
name: erp-herdr-worktree
description: Creates or opens an OpenERP worktree with a Herdr companion pane while the main agent stays in the multirepo workspace. Use when an ERP agent needs to edit a named worktree from a Herdr-managed pane.
---

# ERP Herdr worktree

Use this only after the target worktree is explicit; provide a branch name only
for `create`. The main agent may remain in the multirepo workspace; do **not**
infer the target worktree from its current directory.

## Preconditions

- For `create`, the user has approved creating a worktree under the repository's
  standard worktree directory, as required by the repository worktree policy.
- For `open`, the target is an existing, registered Git worktree.
- The current terminal is a Herdr-managed pane (`HERDR_ENV=1`).
- `bash`, `git`, `python3`, and the `herdr` CLI are available. The helper is bundled with this skill; no user-local installation is needed.

If Herdr is unavailable, continue normally and report that no companion pane
was created.

## Procedure

1. State the explicit absolute path of the target worktree and, if it must be
   created, its branch name.
2. Before editing or running tests, use one command from the directory
   containing this `SKILL.md`:

   ```bash
   # Existing worktree
   <skill-directory>/scripts/erp-herdr-worktree.sh open /absolute/path/to/worktree

   # New worktree and branch
   <skill-directory>/scripts/erp-herdr-worktree.sh create \
     /absolute/path/to/worktree \
     <branch-name>
   ```

   The wrapper validates the target, creates the worktree only when requested,
   then creates a vertical sibling pane rooted at that worktree. It preserves
   focus on the agent pane and reuses a matching companion in the same tab
   instead of creating a duplicate.
3. Use the companion for explicit commands such as inspecting `git diff` or
   running approved tests. Do not start tests, redirect shared addon links, or
   mutate shared ERP state merely by creating the pane.
4. Report the selected worktree and companion-pane result in the handoff.
