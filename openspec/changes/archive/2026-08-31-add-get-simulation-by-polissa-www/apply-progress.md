# Apply Progress: Add Simulation by Policy for WWW

## Status

- Mode: Strict TDD
- Delivery: Single PR with maintainer-approved `size:exception`
- Completed tasks: 11/11
- Application diff: 387 authored changed lines (386 additions, 1 deletion; net +385 across the three allowed application files)
- Deviations from design: None

## Completed Tasks

- [x] 1.1–1.4 Policy contract tests
- [x] 2.1–2.3 Boundary exception, input helper, and public adapter
- [x] 3.1–3.2 Shared-core extraction and fixture consolidation
- [x] 4.1–4.2 Focused and module verification

## Test Command Definitions

All focused commands used this exact prefix and suffix:

```text
PYENV_VERSION=erp WORKSPACE=/home/pau/src scripts/run-tests.sh test_branch_main_1788176993_1539439 -m som_webforms_helpers -t <target> --no-requirements --no-dropdb
```

| ID | `<target>` | RED result | GREEN result |
|---|---|---|---|
| T1 | `tarifes_tests.test__incomplete_simulation_policy__stable_text` | Exit 1; one error, missing `IncompleteSimulationPolicy` | Exit 0; 1 test passed |
| T2 | `tarifes_tests.test__get_simulation_by_polissa_www__incomplete_structure` | Exit 1; one error, missing policy adapter | Exit 0; 1 test passed |
| T3 | `tarifes_tests.test__get_simulation_by_polissa_www__incomplete_powers` | Exit 1; one error, missing policy adapter | Exit 0; 1 test passed |
| T4 | `tarifes_tests.test__get_simulation_by_polissa_www__maps_inputs` | Exit 1; one error, missing policy adapter | Exit 0; 1 test passed |
| T5 | `tarifes_tests.test__get_simulation_by_polissa_www__range_and_equivalence` | Exit 1; one error, missing policy adapter | Exit 0; 1 test passed |

## TDD Cycle Evidence

| Task | RED | GREEN | REFACTOR |
|---|---|---|---|
| 1.1 | T1 and T2 written first and failed | T1 and T2 passed | Shared fixture retained stable text and no-core-call assertions |
| 1.2 | T3 written first and failed | T3 passed | Missing structure and numeric range remained separate concerns |
| 1.3 | T4 written first and failed | T4 passed | Capture assertions consolidated through `_call_policy_simulation` |
| 1.4 | T5 written first and failed | T5 passed | Direct and derived paths share setup while seven legacy tests remain |
| 2.1 | T1 failed before exception existed | T1 passed after exception implementation | Exception follows existing domain-exception style |
| 2.2 | T2 and T3 failed before helper existed | T2 and T3 passed after helper implementation | Validation kept at the model boundary |
| 2.3 | T4 and T5 failed before adapter existed | T4 and T5 passed after adapter implementation | Ordered forwarding removes public-to-public coupling |
| 3.1 | T5 plus seven legacy direct tests protected extraction | Full `tarifes_tests` passed 31/31 | Legacy body mechanically moved to `_calculate_simulation_www` |
| 3.2 | New tests initially used repeated model patches | Focused targets remained GREEN | Fixture and adapter-call helper remove only test duplication |
| 4.1 | T1–T5 recorded the expected missing-symbol failures | T1–T5 each passed individually | Fixture defect from `Mock(name=...)` corrected and target rerun GREEN |
| 4.2 | Baseline legacy suite passed 26/26 before production changes | Final feature suite passed 31/31 | Pre-commit and diff checks passed after extraction |

## Work Unit Evidence

| Work unit | Focused test command and exact result | Runtime harness command/scenario and exact result | Rollback boundary |
|---|---|---|---|
| 1 — Structural eligibility | T2 command above: exit 0, 1/1 passed. T3 also exit 0, 1/1 passed. | N/A — destral transactions exercise the OpenERP model boundary; no route or UI exists. | Revert incomplete-policy tests, `IncompleteSimulationPolicy`, and `_get_simulation_inputs_by_polissa`. |
| 2 — Mapping and equivalence | T4 command above: exit 0, 1/1 passed. T5 also exit 0, 1/1 passed. | N/A — the public OpenERP model method is exercised through destral; no external runtime boundary exists. | Revert mapping/equivalence tests and `get_simulation_by_polissa_www`. |
| 3 — Shared core and regression | Prefix above with target `tarifes_tests`: exit 0, 31/31 passed. | N/A — this is a mechanical internal extraction with no route, UI, or process boundary. | Revert `_calculate_simulation_www` extraction and restore the original `get_simulation_www` body. |

## Additional Verification

| Command | Result |
|---|---|
| `PYENV_VERSION=erp WORKSPACE=/home/pau/src scripts/run-tests.sh test_branch_main_1788176993_1539439 -m som_webforms_helpers -t tarifes_tests --no-requirements --no-dropdb` | Exit 0; 31/31 passed, including all seven legacy direct simulation tests |
| `PYENV_VERSION=erp WORKSPACE=/home/pau/src scripts/run-tests.sh test_branch_main_1788176993_1539439 -m som_webforms_helpers --no-requirements --no-dropdb` | Exit 1; 34 tests ran. All 31 feature tests plus access/view checks passed; only pre-existing `test_translate_modules` failed because the module has no translation files. |
| `PYENV_VERSION=erp pre-commit run --files som_webforms_helpers/giscedata_polissa_tarifa.py som_webforms_helpers/exceptions/som_webforms_exceptions.py som_webforms_helpers/tests/test_tarifes.py` | Exit 0; whitespace, EOF, autoflake, autopep8, and flake8 passed |
| `git diff --check` | Exit 0; no whitespace errors |

## Issues Found

- The full module command has a pre-existing base-test failure: `Module som_webforms_helpers has no translations`. The working tree and `HEAD` contain no module translation files, and this change does not touch translation behavior. All change-specific, legacy simulation, access-rule, and view tests pass.
