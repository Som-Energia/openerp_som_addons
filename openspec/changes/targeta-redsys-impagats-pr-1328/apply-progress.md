# Apply Progress: Final Fresh Review Blockers

Change: `targeta-redsys-impagats-pr-1328`
Mode: Strict TDD
Delivery: single PR with maintainer-approved `size:exception`

## Completed in this batch

- [x] 7.1 Wrapped post-Redsys-success TPV payment/reconciliation in a dedicated savepoint. On local failure the savepoint is rolled back before writing the durable `Redsys targeta recurrent OK pendent conciliacio` marker.
- [x] 7.2 Treated `RestClient.mit_payment` transport/client exceptions as ambiguous manual-review events, writing `Redsys targeta recurrent pendent revisio` notes and excluding those invoices from later recurrent-card search.
- [x] 7.3 Tightened post-lock revalidation so invoices without `payment_type` or without `payment_type.code == COBRAMENT_RECURRENT_TARGETA` are skipped.
- [x] 7.4 Added focused regression tests for all three blockers.

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 7.1 | `som_card_payment/tests/test_redsys_card_collection.py` | Unit/integration with mocks | ✅ 12/12 existing `TestRedsysCardCollection` passed | ✅ `test_charge_invoice_success_reconcile_failure_rolls_back_before_marker` failed before production change | ✅ 15/15 passed after savepoint rollback implementation | ✅ Existing success and reconcile-failure tests cover success and local-failure paths | ✅ Extracted savepoint-name helper and marker constant |
| 7.2 | `som_card_payment/tests/test_redsys_card_collection.py` | Unit/integration with mocks | ✅ 12/12 existing `TestRedsysCardCollection` passed | ✅ Transport exception and search-exclusion assertions failed before production change | ✅ 15/15 passed after manual-review marker/search exclusion | ✅ Transport exception write path plus search exclusion path | ✅ Extracted manual-review format/register helpers |
| 7.3 | `som_card_payment/tests/test_redsys_card_collection.py` | Unit | ✅ 12/12 existing `TestRedsysCardCollection` passed | ✅ Missing/changed payment-type revalidation assertions failed before production change | ✅ 15/15 passed after requiring recurrent-card payment type | ✅ Covers valid recurrent, missing, and changed payment type | ➖ No further refactor needed |

## Commands

- `PYENV_VERSION=erp WORKSPACE=/home/pau/src scripts/run-tests.sh -m som_card_payment -t TestRedsysCardCollection --no-requirements` — PASS, 12 tests baseline.
- `PYENV_VERSION=erp WORKSPACE=/home/pau/src scripts/run-tests.sh -m som_card_payment -t TestRedsysCardCollection --no-requirements` — RED, 15 tests with 4 expected blocker failures before production changes.
- `PYENV_VERSION=erp WORKSPACE=/home/pau/src scripts/run-tests.sh -m som_card_payment -t TestRedsysCardCollection --no-requirements` — PASS, 15 tests after implementation.
- `PYENV_VERSION=erp python -m py_compile som_card_payment/models/account_invoice.py som_card_payment/tests/test_redsys_card_collection.py` — PASS.

## Notes

- No database was dropped or recreated by this batch.
- Test logs continued to show `Not dropping database test_branch_imp_redsys_card_impagats`.
- Failed-card pending XML state remains unchanged as a business decision.
