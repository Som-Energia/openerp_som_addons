# Design: Add Simulation by Policy for WWW

## Technical Approach

Extend `GiscedataPolissaTarifa` in `som_webforms_helpers/giscedata_polissa_tarifa.py`. Place a policy-input helper and a mechanically extracted calculation core immediately after `_round_2`, followed by the existing and new public adapters before `_get_dades_modcontractuals`. The policy helper owns lookup, structural validation, and vocabulary/unit mapping; the core owns all existing selector/range validation, configuration lookup, tax/date handling, economics, rounding, exceptions, and result construction. No `__terp__.py` change is needed: `som_webforms_helpers` already reaches `som_polissa` through `som_facturacio_switching`.

## Architecture Decisions

| Option | Tradeoff | Decision and rationale |
|--------|----------|------------------------|
| Extract `_calculate_simulation_www`; alternatively call one public method from the other or overload the legacy API | Larger mechanical diff, but one calculation path and no public-to-public coupling | Extract the core. Both adapters forward ordered arguments, maximizing sharing while preserving the externally callable legacy contract. |
| Validate/map in the adapter; alternatively let ORM/core failures leak | Adds explicit boundary code, but makes incomplete records deterministic | Add `_get_simulation_inputs_by_polissa`. Structural failures raise `IncompleteSimulationPolicy`; existing calculation failures remain core-owned. |
| Reuse `_is_enterprise`/VAT or the legacy contract-price helper; alternatively apply the dedicated fiscal predicate | Reuse is smaller but wrong at 10 kW and for VAT-bearing titulars | Derive `home` solely from CNAE `9820` and maximum kW `< 10`, matching `calculate_fiscal_position_from_cups`. |

## Data Flow

```text
get_simulation_by_polissa_www
  -> exact policy lookup -> structural validation -> map inputs
  -> _calculate_simulation_www <- get_simulation_www
       -> coefficients/consumption/average price
       -> get_tariff_prices_by_range -> rounded result
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `som_webforms_helpers/giscedata_polissa_tarifa.py` | Modify | Add policy adapter/helper and extract the shared core. |
| `som_webforms_helpers/exceptions/som_webforms_exceptions.py` | Modify | Add `IncompleteSimulationPolicy` with stable text `Policy data required for simulation is incomplete`. |
| `som_webforms_helpers/tests/test_tarifes.py` | Modify | Add RED policy-boundary tests while retaining all seven direct simulation tests. |

## Interfaces / Contracts

```python
def get_simulation_by_polissa_www(
    self, cursor, uid, polissa_id, with_taxes, context
):
```

`get_simulation_www` keeps its exact current signature and defaults. The new adapter verifies an exact policy ID before browsing, without lifecycle-state checks. Required structure is tariff, CUPS, CUPS municipality and subsystem, CNAE code, present invoicing selector, and at least one power row whose period name exists and whose kW value is float-convertible. Missing or malformed structure raises `IncompleteSimulationPolicy` before the core is called. Zero/negative/out-of-range numeric powers are structurally complete and remain subject to the core's inclusive 1–100 kW validation.

The helper maps `atr` to `periods` and `index` to `index`; every other present code raises `InvalidSimulationPricelist`. Powers become `{period_name.lower(): float(kW) * 1000}`. It passes `tarifa.id`, `cups.id_municipi.id`, explicit `fiscal_position_id.id` (or `False`), and `home=False` when fiscal position is explicit; otherwise `home` is the strict CNAE/power predicate. `with_taxes` and the original `context` object, including `None`, are forwarded unchanged so the core retains current normalization and date behavior.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|--------------|----------|
| Unit/RED | Mapping and boundary | Patch the core to capture arguments; cover `atr`/`index`, unsupported present modes, lowercase/W conversion, CUPS municipality, explicit/absent fiscal position, CNAE and 10 kW boundary, tax/context identity, and every missing structure/power component. Assert the core is not called on structural failure. |
| Integration/RED | Equivalence and range ownership | With destral transactions and demo policies, compare both public methods for complete policies in non-active states, explicit/no date, `None` context, taxes, 1/100 kW endpoints, and outside-range errors. |
| Regression | Legacy behavior | Preserve the existing seven direct tests: invalid selector, invalid powers, missing coefficient, and 2.0TD/3.0TD results for both selectors. Run RED, implement minimally to GREEN, then extract/refine the core and rerun the module suite. |
| E2E | Not applicable | No route or UI changes. |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

No migration, dependency, data repair, or feature flag is required. Deploy as an additive model method; rollback reverts the three files together.

## Open Questions

None.
