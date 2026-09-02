## Exploration: Add get_simulation_by_polissa_www

### Current State
`som_webforms_helpers` extends the OpenERP v5 model `giscedata.polissa.tarifa`. Its public `get_simulation_www` method accepts tariff, municipality, per-period powers in watts, a simulation selector (`index` or `periods`), fiscal position, tax/home flags, and context. It validates the selector and a 1–100 kW maximum power, selects the 2.0TD/3.0TD coefficient set from that maximum, estimates annual consumption from the nearest configured lower-or-equal kW entry, obtains tariff prices for the context date, combines current average energy/SSAA prices, and returns a rounded monthly breakdown.

`with_taxes` currently defaults to `None`; its truthiness controls price taxation and the returned `taxes_applied` boolean. `context` defaults to `{}`. `context["date"]` (format `%Y-%m-%d`) anchors the tariff-price day and number of days in the simulated month; absent a date, today is used. The configuration lookups otherwise select their latest records. Repository callers of `get_simulation_www` are limited to seven call sites in `som_webforms_helpers/tests/test_tarifes.py`, although the method is an externally callable webforms API.

Every simulation input can be derived from `giscedata.polissa` as follows:

- `tariff_id`: `polissa.tarifa.id`.
- `municipi_id`: `polissa.cups.id_municipi.id`, the supply location already used by tariff-zone selection elsewhere.
- `powers`: build a dictionary in a simple loop over `polissa.potencies_periode`, using `period.periode_id.name.lower()` as each key and `period.potencia * 1000` as its value, because contract powers are stored in kW while `get_simulation_www` expects watts.
- `pricelist`: map policy mode `"index"` to simulation selector `"index"` and policy mode `"atr"` to simulation selector `"periods"`. This is an explicit translation between two different vocabularies, not a pass-through.
- `fiscal_position`: `polissa.fiscal_position_id.id` when set, otherwise `False`, allowing the existing tariff helper to resolve its default tax position.
- `home`: `polissa.cnae.name == "9820" and max(contracted powers in kW) < 10.0`. This is the existing dedicated fiscal-position predicate in `giscedata.polissa.calculate_fiscal_position_from_cups` (`som_polissa/models/giscedata_polissa.py:973-1002`). It does not inspect titular VAT. `_get_fiscal_position_igic` then consumes this boolean: true selects `home_igic_tax_id`, false selects `industrial_igic_tax_id` (`som_webforms_helpers/giscedata_polissa_tarifa.py:247-267`).
- `with_taxes` and `context`: pass through unchanged; a `None` context must retain the current normalization and today fallback.

#### Verified `home` impact

`home` is observable only when all of these conditions hold: `with_taxes` is truthy; no reduced fiscal position applies; the policy has no explicit `fiscal_position_id`; and the municipality subsystem is not `PE`. Under those conditions `_get_fiscal_position` calls `_get_fiscal_position_igic` (`giscedata_polissa_tarifa.py:271-307`), which chooses the configured domestic or industrial fiscal-position ID from `fiscal_position_igic`. The selected fiscal position is then passed into taxed tariff-product, reactive, social-bonus, and meter price calculations (`giscedata_polissa_tarifa.py:510-652`). Consequently it can change `power_eur`, `meter_eur`, `social_bonus_eur`, and the total for both selectors; for `periods` it can also change `energy_eur` because that path uses the returned current energy prices (`giscedata_polissa_tarifa.py:1013-1044`). The `index` energy component uses the separate average index prices, but its other taxed components still use the selected fiscal position. The simulation only reports `taxes_applied = bool(with_taxes)`, so a wrong domestic/industrial choice is not identified in the result.

The dedicated policy fiscal rule is:

- Canary location is identified from municipality subsystem codes `TF`, `PA`, `LG`, `HI`, `GC`, `FL`, or `TG`.
- Domestic housing is exactly CNAE `9820` with maximum contracted power strictly below 10 kW.
- Otherwise the industrial Canary fiscal position is selected. Exactly 10 kW is industrial because the source uses `< 10.0`.
- Puerto de la Cruz has separate configured fiscal-position IDs but uses the same CNAE/power predicate.

This rule is exercised end-to-end by `som_leads_polissa/tests/test_lead_www_creation.py:374-408`: the shared lead fixture supplies CNAE `9820` and powers 4.4/8.0 kW (`som_leads_polissa/tests/base_som_lead_www.py:60-67`), and the test verifies that the resulting Canary policy receives `fp_canarias_vivienda`. The caller passes policy CUPS, `polissa.cnae.name`, and per-period powers to `calculate_fiscal_position_from_cups` (`som_leads_polissa/models/giscedata_crm_lead.py:290-306`). No titular VAT participates in that call.

Other existing domestic/enterprise rules serve different domains and are not authoritative for IGIC simulation input:

- `giscedata.polissa._is_enterprise` treats CNAE `9810` or `9820` as only an initial domestic candidate, then treats enterprise VAT or any power above 10 kW as enterprise (`som_polissa/models/giscedata_polissa.py:417-433`). Its tests cover CNAE, VAT, and power outcomes (`som_polissa/tests/som_polissa_tests.py:124-147`), and its repository caller uses it to choose a pending-payment/bono-social process, not a fiscal position (`som_polissa/models/giscedata_switching_helpers.py:39-60`). It also differs at exactly 10 kW, which the IGIC fiscal helper classifies as industrial.
- `set_category_eie` derives policy reporting/categories from CNAE `9810`/`9820` and titular VAT, without the power threshold (`som_polissa/models/giscedata_polissa.py:331-395`). The `DOM` category is therefore maintained classification data, not the IGIC fiscal rule.
- SEPA and Infoenergia report helpers use CNAE `9820` together with VAT to label a mandate as business (`som_polissa/report/report_sepa.py:31-43`; `som_infoenergia/report/components/main/main.py:20-33`). They do not calculate electricity fiscal positions.
- `get_tariff_prices_by_contract_id` sets `home = is_enterprise_vat(...)` (`som_webforms_helpers/giscedata_polissa_tarifa.py:1143-1147`). This contradicts both the `home=True` domestic branch and the dedicated CNAE/power fiscal rule, and it has no focused test. It must not be copied as authority for the new method.

For `get_simulation_by_polissa_www`, the authoritative `home` derivation is therefore the `is_vivienda` predicate from `calculate_fiscal_position_from_cups`: CNAE `9820` and maximum policy power below 10 kW. The adapter should still pass the policy's existing `fiscal_position_id` when present; in that case `get_simulation_www` uses the explicit position and `home` is not consulted. When no explicit position exists, the CNAE/power-derived boolean lets the existing date-aware tariff-price path choose domestic versus industrial IGIC without recomputing or overwriting the policy fiscal position. This policy helper is available in the module graph: `som_webforms_helpers` depends on `som_facturacio_switching`, which depends on `som_polissa` (`som_webforms_helpers/__terp__.py:8-17`; `som_facturacio_switching/__terp__.py:11-19`).

#### Verified invoicing-mode boundary

`giscedata.polissa.mode_facturacio` is a database-backed selection, not a closed source-code enum: `_modes_facturacio` returns every configured `giscedata.polissa.mode.facturacio` record (`/home/pau/src/erp/addons/gisce/GISCEMaster/giscedata_facturacio/giscedata_polissa.py:55-66`). Verified module-defined policy codes include `atr`, `index`, `pvpc`, and `tplana` in `giscedata_facturacio`, `giscedata_facturacio_indexada`, `giscedata_facturacio_pvpc`, and `giscedata_facturacio_tarifa_plana` data files respectively. `atr` is the policy default (`giscedata_polissa.py:3212-3217`). Additional configured/custom codes are therefore possible.

The simulation accepts exactly the strings `"index"` and `"periods"`. Any other value raises `InvalidSimulationPricelist` before power or configuration processing (`som_webforms_helpers/giscedata_polissa_tarifa.py:938-945`), with message `Simulation pricelist must be 'index' or 'periods'` (`som_webforms_helpers/exceptions/som_webforms_exceptions.py:35-39`). The method raises this exception directly; it does not convert it into an error dictionary. Therefore forwarding policy mode `atr` unchanged is a mapping defect because ATR is the supported periods simulation. Policy modes such as `pvpc`, `tplana`, or an unknown configured code are intentionally unsupported by the current simulation unless a future requirement defines their economics; they must not be silently mapped to periods. Their expected current failure is the same `InvalidSimulationPricelist` exception.

#### Verified incomplete-policy behavior

OpenERP represents an absent many2one as a falsey `browse_null`; `.id` returns `False` and any other attribute returns `False` (`/home/pau/src/erp/server/bin/osv/orm.py:189-214`). This produces the following concrete boundary behavior:

- `polissa_id` must identify a real policy. Specifically, `browse(..., False)` raises `BrowseRecordError` during browse-record construction (`orm.py:250-270`); other malformed selectors can produce `browse_null` and defer failure to the chained field accesses below.
- Missing `polissa.tarifa` yields `tariff_id=False`; after the existing selector, power, and simulation-configuration checks, tariff pricing attempts `browse(False)` and raises `BrowseRecordError`.
- Missing `polissa.cups` fails immediately while evaluating `polissa.cups.id_municipi.id`: `browse_null.id_municipi` is `False`, so accessing `.id` raises `AttributeError`. If the CUPS exists but its required `id_municipi` is absent, the derived ID is `False` and `res.municipi.browse(False)` raises `BrowseRecordError` in `som_facturacio_switching/res_municipi.py:9-18`.
- A municipality without `subsistema_id` does not fail: `browse_null.code` is `False`, which is treated as non-`PE`. That silently selects insular price lists and, on the automatic-tax path, IGIC (`res_municipi.py:15-21`; `giscedata_polissa_tarifa.py:292-304`).
- An empty `polissa.potencies_periode` produces an empty powers dictionary and the existing `InvalidSimulationPowers`. Each power row normally requires both `periode_id` and numeric `potencia` (`/home/pau/src/erp/addons/gisce/GISCEMaster/giscedata_polissa/giscedata_polissa.py:3138-3150`); corrupt rows missing the period or its name fail while calling `.lower()`, whereas zero/out-of-range powers reach `InvalidSimulationPowers`.
- Missing/false `mode_facturacio` reaches the exact selector validation and raises `InvalidSimulationPricelist`. Normal policies default to `atr`, but draft or inconsistent records can still expose incomplete state.
- Missing `fiscal_position_id` is supported, not an incomplete-data error: its false ID deliberately activates reduced, regional IGIC, or default fiscal-position selection when taxes are requested.
- Missing `cnae` currently does not fail in the dedicated fiscal helper: `polissa.cnae.name` becomes `False`, `is_vivienda` becomes false, and a Canary/Puerto de la Cruz policy silently receives the industrial fiscal position. `_is_enterprise` likewise treats a missing CNAE as enterprise because `False` is not `9810`/`9820`. CNAE is only state-required in `validar` and `modcontractual`, so a draft policy may legitimately lack it at ORM level (`/home/pau/src/erp/addons/gisce/GISCEMaster/giscedata_polissa/giscedata_polissa.py:2471-2479`). Under the accepted product decision, the new adapter must instead reject missing CNAE with the explicit structural domain error before deriving `home`.
- Titular and titular VAT are not required to derive simulation `home`; requiring them for this purpose would reintroduce the disproven VAT-based rule. A policy with a complete CNAE and power structure can be classified for IGIC regardless of titular VAT.

The core policy fields are state-dependent rather than universally required: CUPS and titular become required in the `validar` state; tariff and CNAE are required in `validar` and `modcontractual`; invoicing mode is required in `validar` and `modcontractual`; and `potencies_periode` itself is not declared required (`/home/pau/src/erp/addons/gisce/GISCEMaster/giscedata_polissa/giscedata_polissa.py:2360-2479`; `/home/pau/src/erp/addons/gisce/GISCEMaster/giscedata_facturacio/giscedata_polissa.py:3168-3177`). Per the accepted product decision, policy state itself must not be rejected. Instead, every allowed state must provide the structural data needed by this API: tariff, CUPS/municipality/subsystem, supported invoicing mode, CNAE code, and complete per-period powers. Missing structural data must produce the explicit domain error; missing `fiscal_position_id` remains valid.

CodeGraph located the simulation and policy `_is_enterprise` implementation first, but did not surface the dedicated `calculate_fiscal_position_from_cups` helper, all callers, or focused tests. Targeted filesystem reads/searches supplied those missing details. OpenSpec has `strict_tdd: true`; there are currently no main specs under `openspec/specs/`.

### Affected Areas
- `som_webforms_helpers/giscedata_polissa_tarifa.py` — owns `giscedata.polissa.tarifa`, the current simulation implementation, and the new policy-derived entry point.
- `som_webforms_helpers/tests/test_tarifes.py` — contains all current simulation coverage and should receive RED-first tests for policy input derivation and equivalence.
- `som_polissa/models/giscedata_polissa.py` — contains the authoritative CNAE/power fiscal-position rule and other non-authoritative enterprise/category rules that must be distinguished.
- `som_polissa/tests/som_polissa_tests.py` — proves the broader `_is_enterprise` CNAE/VAT/power behavior but not the dedicated IGIC predicate.
- `som_leads_polissa/tests/test_lead_www_creation.py` — provides existing integration evidence that CNAE `9820` plus sub-10 kW powers selects the Canary housing fiscal position.
- `som_webforms_helpers/models/som_annual_coefficient.py` — unchanged dependency that supplies the latest tariff/pricelist consumption ratios.
- `som_webforms_helpers/models/som_annual_consumption_estimate.py` — unchanged dependency that maps maximum contracted kW to annual estimated consumption.
- `som_webforms_helpers/models/som_last_month_average_price.py` — unchanged dependency that supplies current index or SSAA energy prices.

### Approaches
1. **Extract a private shared simulation core** — move the current calculation unchanged to a private method; keep `get_simulation_www` as an adapter with its existing signature, and make `get_simulation_by_polissa_www` derive contract inputs before invoking the same core.
   - Pros: Satisfies the requested refactor explicitly, shares all validation/calculation code, preserves the existing public API, and isolates policy-field mapping for focused tests.
   - Cons: Moving the existing body creates a larger diff than simple delegation and requires regression tests to catch argument-order mistakes.
   - Effort: Medium

2. **Delegate the new method directly to get_simulation_www** — derive policy inputs and call the existing public method without extracting a core.
   - Pros: Smallest diff and lowest immediate regression risk.
   - Cons: Leaves one public API acting as another API's implementation detail and does not meaningfully refactor the existing method as requested.
   - Effort: Low

3. **Overload get_simulation_www with an optional policy ID** — add branching and optional arguments to the existing signature.
   - Pros: Avoids another private method.
   - Cons: Makes an externally consumed legacy signature ambiguous, mixes input acquisition with calculation, and raises compatibility risk in OpenERP RPC calls.
   - Effort: Medium

### Recommendation
Use approach 1, but keep it mechanical: extract the complete current body into one Python 2.7-compatible private core with the same ordered inputs and no behavioral edits. Both public methods should be thin adapters. The policy adapter should browse `giscedata.polissa` with the supplied context, perform only the mappings documented above, and pass `with_taxes` and `context` through unchanged.

Under strict TDD, first add focused tests for `atr` → `periods`, `index` → `index`, rejection of `pvpc`/unknown modes with `InvalidSimulationPricelist`, lowercase period keys and kW-to-W conversion, CUPS municipality, fiscal-position ID/False, and unchanged tax/context forwarding. Home-classification tests must prove CNAE `9820` with maximum power below 10 kW is domestic, CNAE `9820` at exactly 10 kW is industrial, non-`9820` CNAE is industrial regardless of titular VAT, and missing CNAE raises the accepted structural domain error. Then retain all seven existing `get_simulation_www` tests against the refactored public adapter to prove validation, 2.0TD/3.0TD paths, rounding, and return shape remain stable.

For incomplete policy data, the accepted product decision resolves the previous open question: the adapter must fail with an explicit domain error. Validation must require a real policy, tariff, CUPS with municipality and subsystem, `atr` or `index` invoicing mode, a CNAE record with a code, and at least one complete period-power row with period name and numeric power. Empty/missing powers are structural incompleteness; a complete power set outside the existing 1–100 kW simulation range remains `InvalidSimulationPowers`. Missing `fiscal_position_id` is valid. Titular/VAT is not part of simulation home validation. Any policy state is accepted when this required data is complete.

### Risks
- **Wrong classification authority:** deriving `home` from titular VAT, the `DOM` category, or `_is_enterprise` would apply a different business rule. IGIC housing treatment is specifically CNAE `9820` plus maximum contracted power strictly below 10 kW.
- **Boundary mismatch at 10 kW:** the dedicated fiscal helper uses `< 10.0`, while `_is_enterprise` only switches to enterprise above 10 kW. Reusing `_is_enterprise` would misclassify exactly 10 kW for IGIC.
- **Legacy VAT-only helper:** `get_tariff_prices_by_contract_id` remains contradictory and untested. Copying it can silently change multiple monetary breakdown fields while `taxes_applied` remains true.
- **Mode translation versus unsupported economics:** `atr` must be translated to `periods`; failing to translate it is an adapter bug. `pvpc`, `tplana`, and dynamic/custom modes have no defined simulation behavior and must fail with `InvalidSimulationPricelist`, not be guessed or silently treated as periods.
- **Missing CNAE currently degrades silently:** existing fiscal code treats it as industrial. The accepted explicit-domain-error decision must be enforced before classification, including for draft policies.
- **Coverage gap:** existing tests prove the domestic Canary happy path and the broader `_is_enterprise` behavior, but not the dedicated fiscal helper's non-`9820`, exactly-10-kW, or missing-CNAE branches.
- Moving the calculation body can introduce positional-argument regressions unless both old-path regression tests and new adapter-mapping tests are kept.
- In-repository search cannot detect external RPC consumers, so the existing method name, argument order, defaults, exceptions, and result schema must remain unchanged.

### Ready for Proposal
Yes — the user is correct about the controlling field for Canary housing fiscal treatment: the dedicated source uses CNAE `9820`, not titular VAT. The complete rule also requires maximum contracted power below 10 kW. A proposal may now lock the CNAE/power predicate, ATR/index-only scope, explicit structural domain error, and state-independent eligibility when required data is complete.
