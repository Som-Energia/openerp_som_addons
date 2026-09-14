---
name: erp-herdr-worktree
description: Creates a Herdr companion pane for an existing OpenERP worktree while the main agent stays in the multirepo workspace. Use when an ERP agent needs to edit a named worktree from a Herdr-managed pane.
---

# ERP Herdr worktree companion

Use this only after the worktree that will receive the change is explicit. The
main agent may remain in the multirepo workspace; do **not** infer the target
worktree from its current directory.

## Preconditions

- The target is an existing, registered Git worktree. This skill never creates
  one; follow the repository worktree policy first.
- The current terminal is a Herdr-managed pane (`HERDR_ENV=1`).
- `bash`, `git`, `python3`, and the `herdr` CLI are available. The helper is bundled with this skill; no user-local installation is needed.

If Herdr is unavailable, continue normally and report that no companion pane
was created.

## Procedure

1. State the explicit absolute path of the target worktree.
2. Before editing or running tests, create the companion pane:

   ```bash
   <skill-directory>/scripts/herdr-worktree-companion.sh /absolute/path/to/worktree
   ```

   Resolve `<skill-directory>` to the directory containing this `SKILL.md` before executing the command. The helper creates a vertical sibling pane rooted at that worktree, preserves
   focus on the agent pane, and reuses a matching companion in the same tab
   instead of creating a duplicate.
3. Use the companion for explicit commands such as inspecting `git diff` or
   running approved tests. Do not start tests, redirect shared addon links, or
   mutate shared ERP state merely by creating the pane.
4. Report the selected worktree and companion-pane result in the handoff.
