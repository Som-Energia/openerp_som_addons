# Proposal: Recurrent Card Collection and Failed-Card Impagats Flow

## Intent

Complete the PR #1328 recurrent-card payment path by ensuring card invoices never enter remesa, adding scheduled Redsys recurring collection, and routing failed card charges into the existing impagats workflow with visible invoice notes.

## Scope

### In Scope
- Keep card-payment invoices excluded from automatic and manual remesa/payment-order flows.
- Add a `som_card_payment` cron to collect due recurrent-card invoices through Redsys.
- On Redsys failure, prepend a dated error to invoice additional info/comment and call the pending/impagats flow.
- Add regression tests for remesa exclusion, cron selection, and failure handling.

### Out of Scope
- Reworking PR #1328 lead/payment-card onboarding beyond required integration points.
- Replacing the existing impagats state machine or accounting reconciliation model.
- Building a hosted Redsys one-shot payment flow.

## Capabilities

### New Capabilities
- `recurrent-card-collection`: Recurrent-card invoices are protected from remesa, charged by scheduled Redsys recurring API calls, and moved to impagats when charging fails.

### Modified Capabilities
- None — no existing `openspec/specs/` capabilities are present.

## Approach

Keep `som_card_payment` as the owner of recurrent-card collection. Preserve `account.invoice.afegeix_a_remesa` as the final safety net and add tests covering the manual wizard and automatic remesa selection. Add a cron method in `som_card_payment` that searches open due invoices with payment type `COBRAMENT_RECURRENT_TARGETA`, charges Redsys using `res.partner.creditcard` token/COF data, and handles success/failure through existing invoice/payment and pending APIs. Failure handling MUST be idempotent enough for cron retries.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `som_card_payment/models/account_invoice.py` | Modified | Remesa guard, cron entry point, Redsys charge/failure helpers. |
| `som_card_payment/data/*.xml` | Modified | Cron definition and required config records if approved. |
| `som_card_payment/tests/` | New/Modified | Regression tests for exclusion, Redsys retry, failed-card pending. |
| `som_extend_facturacio_comer/payment_order.py` | Verified | Keep automatic selection limited to direct-debit invoices. |
| `account_invoice_som/wizard/wizard_payment_order_add_invoices.py` | Verified | Manual wizard must remain blocked by central guard. |
| `som_account_invoice_pending/models/account_invoice.py` | Used | Failure calls `set_pending` with confirmed failed-card state. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Redsys recurring API/config is missing locally | High | Confirm credentials, signing, endpoint, and dependency strategy before implementation. |
| Wrong pending state distorts impagats | Medium | Confirm business-approved failed-card initial state before coding. |
| Cron duplicates notes or pending transitions | Medium | Add idempotency rules and retry tests. |

## Rollback Plan

Disable/remove the `som_card_payment` cron XML record, revert Redsys client and failure-routing helpers, and keep/revert only the existing remesa guard behavior. Any invoices already moved to pending must be restored through the standard pending-state administrative workflow.

## Dependencies / Open Questions

- Redsys recurring API credentials/config, signing rules, endpoint, and response-code mapping.
- Approved initial pending state for failed card invoices.
- Existing accounting path to mark successful card collections paid/reconciled.

## Success Criteria

- [ ] Card-payment invoices cannot be added to remesa automatically or manually.
- [ ] Cron attempts Redsys collection only for eligible recurrent-card invoices.
- [ ] Failed charges add dated invoice comment text and enter confirmed impagats state.
- [ ] Tests pass with `scripts/run-tests.sh <database> -m som_card_payment`.
