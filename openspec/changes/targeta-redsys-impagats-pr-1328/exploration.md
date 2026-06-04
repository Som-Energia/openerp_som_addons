## Exploration: targeta-redsys-impagats-pr-1328

### Current State
PR #1328 (`add_payment_card_in_lead`) adds card-recurrent lead support: `billing_payment_method`, temporary tokenized card fields, `som.lead.www.add_payment_card_data`, and activation logic that creates/reuses `res.partner.creditcard` and assigns `som_card_payment.payment_mode_card_recurrent` / `payment_type_card_recurrent` to the contract. The local workspace is on `pr-1290-add-get-simulation-www`, so PR #1328 was inspected through GitHub, while current shared modules were read locally.

The local `som_card_payment` module already contains the card payment data model and an `account.invoice.afegeix_a_remesa` guard that rejects invoices whose `payment_type.code == "COBRAMENT_RECURRENT_TARGETA"`. Automatic remesa selection in `som_extend_facturacio_comer.payment_order.add_invoices_to_payment_order` already searches only `invoice_id.payment_type.code == "RECIBO_CSB"`, so recurrent-card invoices should not be selected there if invoice payment type is set correctly.

No Redsys charging client/API integration exists in `openerp_som_addons`; local code only stores card token/COF metadata. Related Redsys patterns found outside this repo are in `Som-Energia/oficinavirtual`: one-shot hosted form requests, asynchronous notification handling, payment request state transitions, and ERP sync after success. Those are useful patterns but not reusable OpenERP v5 code.

The unpaid workflow is based on `account.invoice` / `giscedata.facturacio.factura` pending states. `set_pending` creates pending history and Som-specific hooks prepend operational notes to `giscedata.facturacio.factura.comment`, which is also the invoice "informació addicional" edited by `wizard.definir.informacio.addicional`.

### Affected Areas
- `som_card_payment/models/account_invoice.py` — Existing central remesa guard for card-recurrent invoices; likely enough for manual/asynchronous remesa insertion, but tests should cover both `account.invoice` and `giscedata.facturacio.factura` paths.
- `som_extend_facturacio_comer/payment_order.py` — Automatic remesa cron search filters `RECIBO_CSB`; verify card invoices are not included and keep this filter explicit.
- `account_invoice_som/wizard/wizard_payment_order_add_invoices.py` — Manual wizard can search invoices by payment type and then calls `afegeix_a_remesa_async`; the central guard should protect it.
- `som_card_payment/models/res_partner_creditcard.py` — Holds token, COF transaction id, masked number, expiry; likely source data for Redsys recurring charge.
- `som_card_payment/models/giscedata_polissa.py` — Adds `creditcard` to contract/modcontractual and validates it belongs to `pagador` when payment type is recurrent card.
- `som_card_payment/data/payment_type_data.xml` and `payment_mode_data.xml` — Defines `COBRAMENT_RECURRENT_TARGETA` and payment mode `COBRAMENT RECURRENT TARGETA`.
- `som_leads_polissa/models/giscedata_crm_lead.py` from PR #1328 — Assigns recurrent-card payment mode/type/card on lead activation.
- `som_leads_polissa/www/som_lead_www.py` from PR #1328 — Resolves web lead payment configuration and stores tokenized card data.
- `som_account_invoice_pending/models/account_invoice.py` — `set_pending` is the entry point to move invoices into impagats and prepend comment text for key terminal states.
- `som_account_invoice_pending/models/update_pending_states.py` and `data/som_account_invoice_pending_data.xml` — Defines and advances Som impagats states such as `default_avis_impagament_pending_state` and `default_esperant_segona_factura_impagada_pending_state`.
- `som_facturacio_comer/wizard/wizard_definir_informacio_addicional.py` — Confirms "informació addicional" is stored in `giscedata.facturacio.factura.comment` with newest text prepended.
- `som_extend_facturacio_comer/payment_order_data.xml` — Good OpenERP v5 cron XML pattern: `ir.cron`, `model`, `function`, `args`, inactive by default.

### Approaches
1. **Extend `som_card_payment` as the card collection owner** — Add the Redsys recurring-charge client/config, cron, invoice search, success/failure handling, comments, and tests inside `som_card_payment`.
   - Pros: Keeps card-specific behavior with card models/payment mode; avoids scattering Redsys logic across billing modules.
   - Cons: `som_card_payment` may need new dependencies on invoice pending/impagats modules and possibly an approved HTTP/Redsys dependency.
   - Effort: Medium/High

2. **Implement cron in billing/impagats modules and call card helpers** — Keep invoice selection and pending-state transitions near existing remesa/impagats code, with only low-level card helpers in `som_card_payment`.
   - Pros: Reuses existing invoice and impagats ownership boundaries.
   - Cons: Card flow becomes split across modules; harder to test and maintain as a coherent payment method.
   - Effort: Medium

### Recommendation
Use Approach 1: make `som_card_payment` own recurring-card collection end-to-end. Add a cron method on a persistent/service model in `som_card_payment`, search due open customer invoices whose payment type is `COBRAMENT_RECURRENT_TARGETA`, charge Redsys with `res.partner.creditcard.token` / `cof_txnid`, and then:

- on success: mark/reconcile the invoice using existing payment mechanisms or a clearly isolated helper;
- on failure: prepend a dated Redsys failure note to `giscedata.facturacio.factura.comment` and call `set_pending` to enter the appropriate Som impagats initial state.

Keep `account.invoice.afegeix_a_remesa` as the final remesa safety net, and add regression tests proving card invoices are excluded from automatic and manual remesa paths.

### Risks
- Redsys recurring API details are not present in this repo; implementation needs approved configuration, request signing, response-code mapping, and dependency strategy before coding.
- Selecting the wrong pending state can skip or distort the existing impagats process; confirm whether failures start at `default_avis_impagament_pending_state`, `default_esperant_segona_factura_impagada_pending_state`, or another business-approved state.
- Failure handling must be idempotent; the cron can retry, so comments and pending-state changes must not duplicate or move invoices repeatedly without rules.
- Payment success accounting/reconciliation is not obvious from local card code; do not mark invoices paid manually without reusing an existing accounting path.
- PR #1328 is large and open; this change should branch from its head to avoid reimplementing/conflicting with lead card fields.

### Ready for Proposal
Yes — but the proposal should explicitly ask business/technical owners to confirm the Redsys recurring charge contract/configuration and the exact initial impagats pending state for failed card collections.
