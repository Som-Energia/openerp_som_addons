# Tasks: Add Simulation by Policy for WWW

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | 520–700 authored additions + deletions |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | Single PR; three work-unit commits |
| Delivery strategy | exception-ok |
| Chain strategy | size-exception |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: size-exception
400-line budget risk: High

Apply gate: maintainer-approved `size:exception` recorded for one PR of 520–700 authored changed lines.

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|---|
| 1 | Deterministic structural eligibility | PR 1 | `scripts/run-tests.sh <database> -m som_webforms_helpers -t tarifes_tests.test__get_simulation_by_polissa_www__incomplete_structure` | N/A—destral transaction is the model boundary | Incomplete-policy tests, exception, and validation helper |
| 2 | Policy mapping and adapter equivalence | PR 1 | `scripts/run-tests.sh <database> -m som_webforms_helpers -t tarifes_tests.test__get_simulation_by_polissa_www__maps_inputs` | N/A—no route/UI; exercise the OpenERP model through destral | Mapping/equivalence tests and public adapter |
| 3 | Shared-core extraction and regression | PR 1 | `scripts/run-tests.sh <database> -m som_webforms_helpers -t tarifes_tests` | N/A—mechanical internal refactor | `_calculate_simulation_www` extraction; restore legacy body if reverted |

## Phase 1: RED — Policy Contract

- [x] 1.1 In `som_webforms_helpers/tests/test_tarifes.py`, add RED cases for absent/nonexistent policy, tariff, CUPS, municipality, subsystem, CNAE/code, and absent selector; assert `IncompleteSimulationPolicy`, its stable text, and no calculation call (“Required structure is missing”).
- [x] 1.2 In `som_webforms_helpers/tests/test_tarifes.py`, add RED cases for empty powers and rows missing period, period name, or float-convertible kW; distinguish complete zero/out-of-range powers as `InvalidSimulationPowers` (“Required structure is missing”, “Power range behavior”).
- [x] 1.3 In `som_webforms_helpers/tests/test_tarifes.py`, add capture tests for ATR/index selectors, PVPC/flat-rate/unknown/custom rejection, lowercase/W powers, CUPS municipality, explicit/absent fiscal position, CNAE `9820` below/exactly 10 kW, other CNAE, and titular/VAT independence (mapping and fiscal scenarios).
- [x] 1.4 In `som_webforms_helpers/tests/test_tarifes.py`, add state-independent, tax/context identity, explicit/no/`None` date, 1/100 kW, outside-range, and direct-versus-policy equivalence tests; preserve all seven direct simulation tests (“Equivalent policy simulation”, “Existing public contract is preserved”).

## Phase 2: GREEN — Boundary and Adapter

- [x] 2.1 Add `IncompleteSimulationPolicy` with text `Policy data required for simulation is incomplete` to `som_webforms_helpers/exceptions/som_webforms_exceptions.py`.
- [x] 2.2 Add `_get_simulation_inputs_by_polissa` to `som_webforms_helpers/giscedata_polissa_tarifa.py` with exact-ID lookup and deterministic structural validation required by tasks 1.1–1.2.
- [x] 2.3 In `som_webforms_helpers/giscedata_polissa_tarifa.py`, complete helper mapping and add `get_simulation_by_polissa_www(cursor, uid, polissa_id, with_taxes, context)`; forward tax/context unchanged and satisfy tasks 1.3–1.4 minimally.

## Phase 3: REFACTOR — Shared Calculation

- [x] 3.1 Mechanically move the current `get_simulation_www` body into `_calculate_simulation_www` in `som_webforms_helpers/giscedata_polissa_tarifa.py`; keep the legacy signature/defaults and route both adapters through the core.
- [x] 3.2 Consolidate only duplicated fixtures/assertions in `som_webforms_helpers/tests/test_tarifes.py`; retain every structural, mapping, equivalence, boundary, and seven legacy direct cases.

## Phase 4: Verification

- [x] 4.1 Run focused destral targets for each new test method with `scripts/run-tests.sh <database> -m som_webforms_helpers -t tarifes_tests.<method>` and record RED/GREEN evidence.
- [x] 4.2 Run `scripts/run-tests.sh <database> -m som_webforms_helpers`; confirm all specification scenarios and seven legacy direct tests pass.
