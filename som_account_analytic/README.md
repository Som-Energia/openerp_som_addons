# Manual journal entry analytics

Install `som_account_analytic` to select an analytic account in the journal entry
line popup and apply existing `account.analytic.default` rules when changing its
accounting account.

## Installation

1. Remove the equivalent temporary ERP source patches and update `account` and
   `account_analytic_distribution` to restore their original database views.
2. Make this addon available in the ERP addons path, restart the service and
   install `som_account_analytic` with its declared dependencies.
3. Add a manual entry line, choose an accounting account with an analytic default,
   and check the analytic account is populated and saved. Also check an account
   without a matching default and the existing distribution column in the list.

## Scope

- Inherits the distribution view so its existing list extension is applied before
  adding the popup field; no ERP source changes are required.
- Normalizes the legacy `account_analytic_id` result to `analytic_account_id`
  after `super()`, preserving taxes, distribution and other inherited values.
- Keeps an already-correct `analytic_account_id` if the parent supplies it.
- Reuses existing rule selection, including its current-date behavior and lack
  of company filtering. No new rules, fields or database migration are introduced.
- Does not change invoice onchanges, inline list editing or import/create APIs.
  The two invoice return fixes from ERP PR #142 remain separate.

## Tests

From the repository checkout with the ERP environment and services available:

```sh
WORKSPACE=/path/to/workspace PYENV_VERSION=erp scripts/run-tests-worktree.sh \
    --addon som_account_analytic -- --no-requirements -m som_account_analytic
```
