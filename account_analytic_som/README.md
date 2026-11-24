# Manual journal entry analytics

Install `account_analytic_som` to select an analytic account in the journal entry
line popup and apply existing `account.analytic.default` rules when changing its
accounting account.

## Installation

1. Remove the equivalent temporary ERP source patches and update `account` and
   `account_analytic_distribution` to restore their original database views.
2. Make this addon available in the ERP addons path, restart the service and
   install `account_analytic_som` with its declared dependencies.
3. Add a manual entry line, choose an accounting account with an analytic default,
   and check the analytic account is populated and saved. Also check an account
   without a matching default and the existing distribution column in the list.

## Scope

- Inherits the distribution view so its existing list extension is applied before
  adding the popup field; no ERP source changes are required.
- Normalizes the legacy `account_analytic_id` result to `analytic_account_id`
  after `super()`, preserving taxes, distribution and other inherited values.
- Keeps an already-correct `analytic_account_id` if the parent supplies it.
- Keeps `account.analytic.default.account_get()` as the shared selector for manual
  entries, invoices, synchronization and any other caller. The inherited domain
  excludes product-specific rules when the caller explicitly passes
  `product_id=False`; matching products and generic rules remain eligible.
  Omitting `product_id` preserves unrestricted product lookup.
- Preserves the parent's ranking, sequence tie-breaking, date filters, analytic
  distribution constraints and lack of company filtering. Manual entry onchanges
  still use the current date. No new rules, fields or database migration are needed.
- Does not replace invoice onchanges, inline list editing or import/create APIs;
  their existing `account_get()` calls use the shared matching behavior.
  The two invoice return fixes from ERP PR #142 remain separate.

## Tests

From the repository checkout with the ERP environment and services available:

```sh
OPENERP_WORKTREE_TEST_WORKSPACE=/path/to/workspace PYENV_VERSION=erp \
    scripts/run-tests-worktree.sh --addon account_analytic_som -- \
    --no-requirements -m account_analytic_som
```
