## Verification Report

Change: `targeta-redsys-impagats-pr-1328`
Mode: OpenSpec / Strict TDD

### Command Evidence

| Command | Exit status | Result |
|---|---:|---|
| `PYENV_VERSION=erp WORKSPACE=/home/pau/src scripts/run-tests.sh -m som_card_payment -t TestRedsysCardCollection --no-requirements` | 0 | PASS: 16 tests, OK |
| `PYENV_VERSION=erp WORKSPACE=/home/pau/src scripts/run-tests.sh -m som_card_payment -t TestCardPaymentNotInRemesa.test_add_to_remesa_raises_for_card_recurrent_invoice --no-requirements` | 0 | PASS: 1 test, OK |
| `PYENV_VERSION=erp python -m py_compile som_card_payment/models/account_invoice.py som_card_payment/tests/test_redsys_card_collection.py som_card_payment/tests/test_remesa_card_payment.py` | 0 | PASS: no output |

### Database Reuse Evidence

- Redsys collection test log includes `Not dropping database test_branch_imp_redsys_card_impagats`.
- Remesa exclusion test log includes `Not dropping database test_branch_imp_redsys_card_impagats`.
- The required commands passed no explicit DB name and did not set `OPENERP_TEST_DB_FRESH=1`.

### Source Inspection Notes

- Unexpected per-invoice cron exceptions are logged via `logger.exception(...)` while the cron rolls back the invoice savepoint and continues.
- `_search_recurrent_card_invoice_ids()` excludes success-pending-reconcile, manual-review, and regular Redsys KO/failure markers before selecting invoices for future cron runs.
- Focused tests cover the cleanup paths: `test_cron_collect_recurrent_card_invoices_logs_unexpected_exception` and `test_search_recurrent_card_invoice_ids_checks_due_date_and_card`.

### Failures

None. The expected logged exception inside the cron-isolation test is test data and the test passed.

### Verdict

PASS
