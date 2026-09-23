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
- Amb `HERDR_ENV=1`, no useu mai `git worktree add` directament, tampoc per crear el worktree: el wrapper d'aquesta skill és obligatori per a `create` i `open`.

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
   then creates or reuses a vertical sibling pane rooted at that worktree. It
   preserves focus on the agent pane, names that pane `agent`, and reuses a
   matching companion in the same tab instead of creating a duplicate. It
   records both the active worktree basename and companion pane ID as caller
   metadata.
4. If no matching companion exists, the helper may retarget exactly one
   same-tab pane labeled `worktree · ...` rather than creating a split. It only
   retargets a pane when Herdr reports a single foreground process that is the
   pane shell itself (`sh`, `bash`, `zsh`, or `fish`). The helper never changes
   a busy or ambiguous pane; it fails rather than sending it a command or
   creating another pane. After sending a safely quoted `cd -- <worktree>`, it
   waits until Herdr reports the new foreground working directory before
   relabeling the pane. If that confirmation fails, no pane is created.
5. Use the companion for explicit commands such as inspecting `git diff` or
   running approved tests. Do not start tests, redirect shared addon links, or
   mutate shared ERP state merely by creating the pane.
6. Report the selected worktree and companion-pane result in the handoff.
