# Tasks: Recurrent Card Collection and Failed-Card Impagats Flow

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 520-750, below selected 800 but above 400 guard |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | Prefer PR 1 tests/remesa, PR 2 Redsys cron, PR 3 success/failure flow; current strategy requests single PR |
| Delivery strategy | single-pr |
| Chain strategy | size-exception |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: size-exception
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Remesa protections and RED tests | PR 1 | Base PR #1328 branch/head; destral remesa coverage |
| 2 | Redsys selection, adapter, config, cron | PR 2 | Depends on Unit 1; mock Sermepa `RestClient.mit_payment` |
| 3 | Success/failure processing and retry tests | PR 3 | Depends on Unit 2; pending/comment integration |

## Phase 1: Preparation and RED Tests

- [x] 1.1 Prep branch only: create `IMP_redsys-card-impagats` from PR #1328 head/base (`add_payment_card_in_lead`, base `main`) before implementation.
- [x] 1.2 Add failing remesa tests in `som_card_payment/tests/test_remesa_card_payment.py` for automatic selection and manual wizard rejection.
- [x] 1.3 Create failing `som_card_payment/tests/test_redsys_card_collection.py` for eligible/ineligible cron selection and one Redsys call per invoice.
- [x] 1.4 Add failing success, failure-note, pending, and idempotent retry scenarios in `test_redsys_card_collection.py`.

## Phase 2: Remesa Exclusion Reinforcement

- [x] 2.1 Keep `som_card_payment/models/account_invoice.py::afegeix_a_remesa` as final guard for `COBRAMENT_RECURRENT_TARGETA` invoices.
- [x] 2.2 Verify `som_extend_facturacio_comer/payment_order.py` automatic domain only selects `RECIBO_CSB`; adjust only if RED test proves leakage.
- [x] 2.3 Verify `account_invoice_som/wizard/wizard_payment_order_add_invoices.py` cannot bypass `afegeix_a_remesa`; adjust only if RED test proves bypass.

## Phase 3: Redsys Adapter, Config, and Cron

- [x] 3.1 Add `_search_recurrent_card_invoice_ids` and `_cron_collect_recurrent_card_invoices` to `som_card_payment/models/account_invoice.py`.
- [x] 3.2 Add Sermepa helper methods in `account_invoice.py` to read Redsys config, build MIT params, call `RestClient.mit_payment`, and map `Ds_Response`.
- [x] 3.3 Create inactive `som_card_payment/data/cron_data.xml` for scheduled card collection.
- [x] 3.4 Update `som_card_payment/__terp__.py` to load cron XML and approved dependencies needed for pending/payment APIs.

## Phase 4: Payment Result Handling

- [x] 4.1 Implement success path in `account_invoice.py` using existing TPV payment/reconciliation API; never write paid state directly.
- [x] 4.2 Implement `_register_redsys_failure` to prepend dated invoice `comment` text without deleting existing information.
- [x] 4.3 Route failed charges to the approved impagats pending state via existing `set_pending`, skipping duplicate transitions for same order/response marker.

## Phase 5: Verification

- [x] 5.1 Run targeted destral tests for remesa and Redsys collection with reusable DB and `--no-requirements`.
- [x] 5.2 Run Python 2 `py_compile` on changed Python files to keep Python 2.7/OpenERP 5 compatibility.
- [ ] 5.3 Run flake8/pre-commit checks when available locally; current environment reports `flake8: command not found` / `No module named flake8`.

## Phase 6: Fresh Review Blocker Fix Batch

- [x] 6.1 Add a DB row-level `FOR UPDATE NOWAIT` guard before `RestClient.mit_payment` so concurrent cron workers skip invoices already owned by another transaction.
- [x] 6.2 Add per-invoice savepoint/commit isolation in the cron loop so later invoice exceptions cannot roll back earlier local payment/failure results.
- [x] 6.3 Add focused regression coverage for lock conflicts and per-invoice cron isolation.
- [x] 6.4 Pending-state choice for failed card charges remains a business decision; no dependency-unsafe `som_account_invoice_pending` state was introduced.

## Phase 7: Final Fresh Review Blockers

- [x] 7.1 Wrap local TPV payment/reconciliation after Redsys success in a dedicated savepoint, rollback it on local failure, then persist the success-pending-reconciliation marker for cron commit.
- [x] 7.2 Treat `RestClient.mit_payment` transport/client exceptions as ambiguous manual-review events instead of regular Redsys KO, and exclude marked invoices from recurrent-card search.
- [x] 7.3 Revalidate locked invoices with an explicit recurrent-card `payment_type.code` match before Redsys submission.
- [x] 7.4 Add focused regression coverage for the savepoint rollback marker, ambiguous transport marker/search exclusion, and payment-type revalidation.

## Phase 8: Final Narrow Cleanup Warnings

- [x] 8.1 Log unexpected per-invoice cron exceptions with OpenERP-compatible logging while preserving continue-to-next-invoice isolation.
- [x] 8.2 Exclude confirmed Redsys KO/failure-marked invoices from recurrent-card search and add focused regression coverage proving they are skipped.

## Phase 9: Greptile Review Fixes

- [x] 9.1 Revalidate Redsys success/manual/KO markers after the invoice row lock before any new external charge.
- [x] 9.2 Deduplicate `account.invoice` IDs returned from factura lookup before cron processing.
- [x] 9.3 Roll back the per-invoice cron savepoint for lock-skipped/no-op invoices and commit only invoices that wrote durable state.
- [x] 9.4 Document that KO markers intentionally block automatic retries until operators resolve and clear the marker.
