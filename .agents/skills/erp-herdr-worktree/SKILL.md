---
name: erp-herdr-worktree
description: Creates or opens an OpenERP worktree with a companion pane in Herdr TUI or Herdr App / herdr-core while the main agent stays in the multirepo workspace. Use when an ERP agent needs to edit a named worktree from either Herdr environment.
---

# ERP Herdr worktree

Use this only after the target worktree is explicit; provide a branch name only
for `create`. The main agent may remain in the multirepo workspace; do **not**
infer the target worktree from its current directory.

## Preconditions

- For `create`, the user has approved creating a worktree under the repository's
  standard worktree directory, as required by the repository worktree policy.
- For `open`, the target is an existing, registered Git worktree.
- The current terminal belongs to either **Herdr TUI** (`HERDR_ENV=1` and
  `HERDR_PANE_ID`) or **Herdr App / herdr-core** (`HC_TERMINAL_ID`). These are
  different APIs: a core terminal address such as `t7` is **not** a pane ID.
- `bash`, `git`, and `python3` are available. TUI needs `herdr`; App needs
  `herdr-app` and `hc`. Helpers are bundled; no user-local installation is needed.
- In either environment, never use `git worktree` commands directly, including
  to create a worktree: this wrapper is mandatory for `create` and `open`.

The wrapper selects the backend automatically, preferring TUI when
`HERDR_ENV=1` (including a TUI nested inside hc). It never falls back to the
other backend after a failure. App resolves the caller via `herdr-app ls`,
not the focused pane, and verifies it before `create` mutates Git. A hidden
terminal, unavailable app/core, missing metadata, or remote app space causes
an error; stop rather than bypassing the wrapper. The current App backend
supports local worktrees only.

The normal repository worktree flow applies only outside both environments.
Optional executable overrides: `HERDR_BIN_PATH` (TUI), `HERDR_APP_BIN_PATH`
and `HC_BIN_PATH` (App).

## Procedure

1. State the explicit absolute path of the target worktree and, if it must be
   created, its branch name.
2. Before creating a new worktree, synchronize shared dependencies from the
   primary checkout using `erp-workspace-sync`:

   ```bash
   /absolute/path/to/openerp_som_addons/scripts/sync-workspace-repositories.sh
   ```

   Pass an explicit one-off exception when the development needs one, for
   example `--branch erp=developer`. The script must finish successfully before
   the worktree is created; it refuses dirty, absent, or divergent dependencies.
   `--persist` at this point writes the primary checkout's local override, not
   the new worktree's. To persist the exception in the new worktree, run its
   own `scripts/sync-workspace-repositories.sh --branch erp=developer --persist`
   after creation. Skip synchronization for documentation/CI/skill metadata
   changes that do not need the ERP environment, per repository policy. It is
   also not required for `open`, which must not change shared repositories.
3. Before editing or running tests, use one command from the directory
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
   preserves focus and reuses a matching companion in the same tab instead of
   creating a duplicate. The caller itself is never considered a companion.
   TUI names the caller `agent` and records the worktree basename and companion
   pane ID as caller metadata, as before. App uses explicit pane IDs for layout
   commands and core terminal addresses for inspection and labels. It records
   `erp.worktree` (absolute path) and `erp.companion` (terminal address) on the
   caller, and `erp.role=worktree-companion`, `erp.owner`, `erp.worktree` on the
   companion. App checks the foreground cwd, not the stale launch directory.
   For a new App split the caller tab must be shown; focus is restored after
   splitting. No other tab is selected implicitly.
4. **TUI:** If no matching companion exists, the helper may retarget exactly one
   same-tab pane labeled `worktree · ...` rather than creating a split. It only
   retargets a pane when Herdr reports a single foreground process that is the
   pane shell itself (`sh`, `bash`, `zsh`, or `fish`). The helper never changes
   a busy or ambiguous pane; it fails rather than sending it a command or
   creating another pane. After sending a safely quoted `cd -- <worktree>`, it
   waits until Herdr reports the new foreground working directory before
   relabeling the pane. If that confirmation fails, no pane is created.

   **App:** Matching companions are reused without sending commands. An existing
   labeled companion at another/unknown cwd causes a safe error, not a `cd` or
   another split: core's foreground summary cannot prove that an entire process
   group is an idle shell. Resolve that companion explicitly before retrying.
   Multiple matching/labeled companions are also rejected as ambiguous. Do not
   close, kill, or restart user terminals to work around an error.
5. Use the companion for explicit commands such as inspecting `git diff` or
   running approved tests. Do not start tests, redirect shared addon links, or
   mutate shared ERP state merely by creating the pane.
6. Report the selected worktree and companion-pane result in the handoff.

## Regression tests

Run the isolated CLI-mock tests (no ERP services, live app, or shared addons):

```bash
python3 <skill-directory>/tests/test_worktree_companion.py
```

App commands were verified against Herdr App 0.1.12 / hc 0.1.17; the legacy
`herdr pane` interface remains supported.
