# Design: Recurrent Card Collection and Failed-Card Impagats Flow

## Technical Approach

Implement from PR #1328 head (`add_payment_card_in_lead`, base `main`) so lead card fields, `res.partner.creditcard`, and card payment mode/type are present. Keep `som_card_payment` as owner: it already blocks `account.invoice.afegeix_a_remesa` for `COBRAMENT_RECURRENT_TARGETA`, stores token/COF data, and validates contract/card ownership. No branch is created in this phase.

## Architecture Decisions

| Option | Tradeoff | Decision |
|---|---|---|
| Put cron in billing/impagats modules | Closer to remesa/pending, but splits card behavior | Add cron and helpers to `som_card_payment/models/account_invoice.py`; add dependency on `som_account_invoice_pending` only if needed for XML/state references. |
| Vendor Redsys code | More control, but duplicates maintained code | Reuse installed `sermepa` package aligned with `/home/pau/src/sermepa` 1.2.0 `RestClient.mit_payment`; wrap it in a small `som_card_payment` helper for config, request building, and response interpretation. |
| Mark success by direct state writes | Fast, but unsafe accounting | Use existing invoice payment/reconciliation API (`pay_and_reconcile`/payment wizard pattern) with TPV journal; never set paid manually. |
| On failure call pending every retry | Simple, but duplicates history/notes | Add idempotent failure handling: prepend a Redsys note only if the same order/response marker is absent and call `set_pending` only when invoice is not already in the target failed-card pending state. |

## Data Flow

```text
Manual/auto remesa -> account.invoice.afegeix_a_remesa -> reject card invoices

ir.cron -> account.invoice._cron_collect_recurrent_card_invoices
        -> _search_recurrent_card_invoice_ids
        -> _charge_invoice_by_redsys(invoice)
        -> success: _pay_invoice_by_tpv
        -> failure: _register_redsys_failure + set_pending
```

## File Changes

| File | Action | Description |
|---|---|---|
| `som_card_payment/models/account_invoice.py` | Modify | Add cron entry point, invoice domain, Redsys wrapper calls, success/failure helpers; keep remesa guard. |
| `som_card_payment/data/cron_data.xml` | Create | Inactive `ir.cron` calling `_cron_collect_recurrent_card_invoices`, same pattern as `som_extend_facturacio_comer/payment_order_data.xml`. |
| `som_card_payment/__terp__.py` | Modify | Load cron XML and add approved dependencies if required. |
| `som_card_payment/tests/test_redsys_card_collection.py` | Create | Destral tests for selection, success, failure, and retry idempotency. |
| `som_card_payment/tests/test_remesa_card_payment.py` | Modify | Add automatic remesa/wizard regression coverage. |

## Interfaces / Contracts

```python
def _cron_collect_recurrent_card_invoices(self, cursor, uid, context=None):
    return True

def _search_recurrent_card_invoice_ids(self, cursor, uid, limit=None, context=None):
    domain = [
        ("state", "=", "open"),
        ("type", "like", "out_%"),
        ("date_due", "<=", today),
        ("payment_order_id", "=", False),
        ("payment_type.code", "=", "COBRAMENT_RECURRENT_TARGETA"),
        ("residual", ">", 0),
    ]
```

Build Redsys MIT params from invoice amount cents, unique order (`invoice.id` plus attempt/date), merchant config from `res.config`, and card `token` as `Ds_Merchant_Identifier`; set `Ds_Merchant_Cof_INI='N'`, `Ds_Merchant_Cof_Type='C'`, `Ds_Merchant_Excep_SCA='MIT'`, `Ds_Merchant_DirectPayment='true'`. Treat `Ds_Response` 0-99 as success; otherwise failure.

Failure note prepended to invoice `comment` / informació addicional:

```text
YYYY-MM-DD - Redsys targeta recurrent KO - factura {number} - ordre {order} - codi {Ds_Response|HTTP} - {message}
```

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | Redsys params/response mapping, note de-duplication | Mock wrapper/RestClient in destral. |
| Integration | Cron selection, success payment via TPV journal, failure `set_pending` | `scripts/run-tests.sh <database> -m som_card_payment`. |
| E2E | PR #1328 lead creates card-backed contract invoice | Covered by PR #1328 tests plus one regression if branch has fixtures. |

## Migration / Rollout

No data migration required unless adding stored retry/audit fields. Cron must be installed inactive; enable only after Redsys credentials, endpoint, terminal, TPV journal/account, and pending state are configured.

## Open Questions

- [ ] Confirm exact failed-card initial pending state: likely `som_account_invoice_pending.default_avis_impagament_pending_state`, but business must approve.
- [ ] Confirm Redsys production/test config keys and whether `sermepa==1.2.0` is available in the ERP runtime.
