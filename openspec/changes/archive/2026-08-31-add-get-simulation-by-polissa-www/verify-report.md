```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:6dec08f319d41626b708a6789e602f31a59ff90d354d8b67ac0cda217f15c859
verdict: pass_with_warnings
blockers: 0
critical_findings: 0
requirements: 5/5
scenarios: 13/13
test_command: 'PYENV_VERSION=erp WORKSPACE=/home/pau/src scripts/run-tests.sh test_branch_main_1788176993_1539439 -m som_webforms_helpers -t tarifes_tests --no-requirements --no-dropdb'
test_exit_code: 0
test_output_hash: sha256:1fe81fd039f09448e5c9d16cfd6b6af7bb4a491fbb233314f1da692b3332ed85
build_command: 'PYENV_VERSION=erp pre-commit run --files som_webforms_helpers/giscedata_polissa_tarifa.py som_webforms_helpers/exceptions/som_webforms_exceptions.py som_webforms_helpers/tests/test_tarifes.py && git diff --check'
build_exit_code: 0
build_output_hash: sha256:9c4b38c5f88e21d5d08fec3dd8782039373f9ef9adb46783a27c8265e56533dc
```

## Verification Report

**Change**: `add-get-simulation-by-polissa-www`
**Version**: N/A
**Mode**: Strict TDD
**Persistence**: OpenSpec / repo-local
**Candidate identity**: `sha256:6dec08f319d41626b708a6789e602f31a59ff90d354d8b67ac0cda217f15c859`
**Review status**: `disabled/unmanaged` (`rdd_disabled`); no approval is claimed and no review was launched
**Skill resolution**: `paths-injected` — `sdd-verify`, `strict-tdd-verify`, and repository `erp-test`

### Completeness

The retrieved specification contains 5 requirements and 13 scenarios. Counts were taken directly from the specification, not from dispatcher estimates.

| Metric | Value |
|---|---:|
| Requirements total / compliant | 5 / 5 |
| Scenarios total / compliant | 13 / 13 |
| Tasks total | 11 |
| Tasks complete | 11 |
| Tasks incomplete | 0 |
| Changed application files | 3 |
| Authored application diff | 387 lines (386 additions, 1 deletion) |
| Approved application limit | 700 lines |

All task checkboxes in `tasks.md` are checked. The actual three-file application diff matches `apply-progress.md` and remains within the approved size exception.

### Build & Tests Execution

#### Focused tariff suite — PASS

```text
PYENV_VERSION=erp WORKSPACE=/home/pau/src scripts/run-tests.sh test_branch_main_1788176993_1539439 -m som_webforms_helpers -t tarifes_tests --no-requirements --no-dropdb
Exit: 0
Result: 31/31 destral tests passed; 45/45 server examples also passed
Output SHA-256: 1fe81fd039f09448e5c9d16cfd6b6af7bb4a491fbb233314f1da692b3332ed85
```

The runtime log names every new policy-derived test and all seven legacy direct-simulation tests as `ok`.

#### Full module suite — NON-ZERO, proven base-only translation check

```text
PYENV_VERSION=erp WORKSPACE=/home/pau/src scripts/run-tests.sh test_branch_main_1788176993_1539439 -m som_webforms_helpers --no-requirements --no-dropdb
Exit: 1
Result: 33/34 destral tests passed; only test_translate_modules failed
Failure: AssertionError: Module som_webforms_helpers has no translations
Output SHA-256: e8c360ecf3f595c25231a0ba6b5fa15bc09dbac0db64c66457de63ecb58a5e46
```

This command is not reported as passing. Causality was independently checked: `destral/testing.py:250-257` constructs `<module>/i18n` and fails solely when that directory does not exist; both the current worktree glob and `git ls-tree -r HEAD -- som_webforms_helpers` show no `i18n`, `.po`, or `.pot` path; and the candidate changes exactly the exception, tariff implementation, and tariff test files. The failing precondition therefore exists in `HEAD` and is unrelated to the candidate.

#### Coverage — PASS with low whole-file percentages

```text
PYENV_VERSION=erp WORKSPACE=/home/pau/src scripts/run-tests.sh test_branch_main_1788176993_1539439 -m som_webforms_helpers -t tarifes_tests --no-requirements --no-dropdb --report-coverage
Exit: 0
Result: 31/31 tests passed; module line coverage 59%
Output SHA-256: f78c151d75cea6ec81ee5d284b717718ad5d989db1ce0f6a6425b0dfeb1918e2
```

#### Check-only lint and diff validation — PASS

```text
PYENV_VERSION=erp pre-commit run --files som_webforms_helpers/giscedata_polissa_tarifa.py som_webforms_helpers/exceptions/som_webforms_exceptions.py som_webforms_helpers/tests/test_tarifes.py && git diff --check
Exit: 0
Result: trailing whitespace, EOF, autoflake, autopep8, and flake8 passed; YAML/XML hooks had no applicable files; git diff --check passed
Output SHA-256: 9c4b38c5f88e21d5d08fec3dd8782039373f9ef9adb46783a27c8265e56533dc
```

### Spec Compliance Matrix

| Requirement | Scenario | Runtime covering test | Result |
|---|---|---|---|
| Policy-derived public operation | Equivalent policy simulation | `test_tarifes.py > test__get_simulation_by_polissa_www__range_and_equivalence` | ✅ COMPLIANT |
| Policy-derived public operation | Existing public contract is preserved | Seven `test__get_simulation_www__*` regression tests plus `test__get_simulation_by_polissa_www__range_and_equivalence` | ✅ COMPLIANT |
| Policy structural eligibility | Required structure is missing | `test__get_simulation_by_polissa_www__incomplete_structure`; `test__get_simulation_by_polissa_www__incomplete_powers` | ✅ COMPLIANT |
| Policy structural eligibility | Fiscal position is absent | `test__get_simulation_by_polissa_www__maps_inputs` | ✅ COMPLIANT |
| Selector and power mapping | Supported selectors are mapped | `test__get_simulation_by_polissa_www__maps_inputs` | ✅ COMPLIANT |
| Selector and power mapping | Unsupported selector is distinguished from absence | `test__get_simulation_by_polissa_www__maps_inputs`; `test__get_simulation_by_polissa_www__incomplete_structure` | ✅ COMPLIANT |
| Selector and power mapping | Powers are normalized | `test__get_simulation_by_polissa_www__maps_inputs` | ✅ COMPLIANT |
| Selector and power mapping | Power range behavior | `test__get_simulation_by_polissa_www__incomplete_powers`; `test__get_simulation_by_polissa_www__range_and_equivalence` | ✅ COMPLIANT |
| Location and fiscal classification | Explicit fiscal position and supply location | `test__get_simulation_by_polissa_www__maps_inputs` | ✅ COMPLIANT |
| Location and fiscal classification | Domestic classification | `test__get_simulation_by_polissa_www__maps_inputs` | ✅ COMPLIANT |
| Location and fiscal classification | Industrial classification boundaries | `test__get_simulation_by_polissa_www__maps_inputs` | ✅ COMPLIANT |
| Tax and context passthrough | Explicit date and taxes are preserved | `test__get_simulation_by_polissa_www__maps_inputs`; `test__get_simulation_by_polissa_www__range_and_equivalence` | ✅ COMPLIANT |
| Tax and context passthrough | No date is supplied | `test__get_simulation_by_polissa_www__range_and_equivalence` | ✅ COMPLIANT |

**Compliance summary**: 13/13 scenarios compliant at runtime; 5/5 requirements complete.

### Correctness (Static Evidence)

| Requirement | Status | Evidence |
|---|---|---|
| Policy-derived public operation | ✅ Implemented | `get_simulation_by_polissa_www(cursor, uid, polissa_id, with_taxes, context)` performs no state check and forwards to the shared core. The legacy `get_simulation_www` signature and defaults are byte-equivalent to `HEAD`; its original body was mechanically renamed to `_calculate_simulation_www` and the public wrapper forwards ordered arguments. |
| Policy structural eligibility | ✅ Implemented | `_get_simulation_inputs_by_polissa` performs exact-ID search and validates policy, tariff, CUPS, municipality, subsystem, CNAE/code, mode, powers, period/name, and float-convertible values before core invocation. `IncompleteSimulationPolicy` has the specified stable text; a missing fiscal position remains valid. |
| Selector and power mapping | ✅ Implemented | The helper maps `atr`/`index`, rejects every other present mode with `InvalidSimulationPricelist`, lowercases period names, converts kW to W, and leaves numeric range enforcement in the shared core. |
| Location and fiscal classification | ✅ Implemented | Municipality comes from CUPS; explicit fiscal position IDs are preserved; otherwise `home` is exactly CNAE `9820` and maximum kW `< 10`, independent of titular/VAT. |
| Tax and context passthrough | ✅ Implemented | The adapter forwards the original `with_taxes` and `context` objects unchanged to `_calculate_simulation_www`. |

### Coherence (Design)

| Decision | Followed? | Evidence |
|---|---|---|
| Shared private calculation core | ✅ Yes | Both public adapters call `_calculate_simulation_www`; no public-to-public coupling was introduced. |
| Boundary helper and dedicated exception | ✅ Yes | Lookup, validation, mapping, and `IncompleteSimulationPolicy` remain outside the economics core. |
| Dedicated fiscal predicate | ✅ Yes | No `_is_enterprise`, titular, or VAT dependency is used. |
| Additive rollout without migration | ✅ Yes | Only the three designed application files changed; no manifest, migration, route, or UI change exists. |
| Public signature compatibility | ✅ Yes | `get_simulation_www` keeps the exact pre-change positional parameters and defaults; the new public method matches the designed signature. |

### TDD Compliance

| Check | Result | Details |
|---|---|---|
| TDD evidence reported | ✅ | `apply-progress.md` contains a TDD Cycle Evidence table for all 11 tasks and exact T1–T5 RED/GREEN command outcomes. |
| All tasks have tests | ✅ | 11/11 tasks map to the changed tariff test file and recorded focused/module runs. |
| RED confirmed (tests exist) | ✅ | All five reported T1–T5 methods exist in `test_tarifes.py`; recorded RED failures identify the missing production symbols. |
| GREEN confirmed (tests pass) | ✅ | All five feature methods and all seven legacy direct methods passed in the independent 31/31 runtime run. |
| Triangulation adequate | ✅ | The five feature methods exercise multiple structure, selector, power, fiscal, context, and range variants covering all 13 scenarios. |
| Safety net for modified files | ✅ | The recorded 26/26 pre-change baseline and seven retained legacy simulation tests protect the three modified files; the current tariff suite passes 31/31. |

**TDD Compliance**: 6/6 checks passed.

### Test Layer Distribution

| Layer | Tests | Files | Tools |
|---|---:|---:|---|
| Unit/model-boundary | 4 | 1 | destral + `mock` |
| Integration/regression | 8 | 1 | destral transactions (one policy/direct equivalence method plus seven legacy direct methods) |
| E2E | 0 | 0 | Not applicable; no route or UI changed |
| **Total relevant methods** | **12** | **1** | |

### Changed File Coverage

Destral reports whole-file line coverage, not changed-line or branch coverage. Tests are intentionally omitted by its coverage configuration.

| File | Line % | Branch % | Uncovered Lines | Rating |
|---|---:|---:|---|---|
| `som_webforms_helpers/exceptions/som_webforms_exceptions.py` | 31% | N/A | Runner did not emit line ranges | ⚠️ Low |
| `som_webforms_helpers/giscedata_polissa_tarifa.py` | 67% | N/A | Runner did not emit line ranges | ⚠️ Low |
| `som_webforms_helpers/tests/test_tarifes.py` | Omitted | N/A | Test files excluded by runner | ➖ Not measured |

**Average instrumented changed-production-file coverage**: 49%.
**Whole-module line coverage**: 59%.
These coarse percentages include substantial unchanged legacy code; runtime scenario compliance is established separately by the passing targeted tests.

### Assertion Quality

The changed tests call production code, assert concrete values or concrete domain exceptions, verify the core is not called on structural failures, and use non-empty fixed case sets. No tautologies, orphan empty assertions, type-only assertions, ghost loops, smoke-only assertions, or implementation-detail-only assertions were found.

**Assertion quality**: ✅ All assertions verify real behavior.

### Quality Metrics

**Linter**: ✅ No errors or warnings in changed files.
**Type Checker**: ➖ Not available/configured for this Python 2.7 OpenERP module.
**Diff validation**: ✅ `git diff --check` passed.

### Issues Found

**CRITICAL**: None.

**WARNING**:
1. The full module command exits 1 because the base module has no `i18n` directory. This is a real non-zero check and is not called a pass, but source/test inspection proves its failing precondition exists in `HEAD` and is outside the three-file candidate.
2. Destral's coarse whole-file coverage is below 80% for both changed production files (31% and 67%); it cannot isolate authored changed lines in report-only mode.

**SUGGESTION**: None.

### Verdict

**PASS WITH WARNINGS**

All 5 requirements and 13 scenarios have passing runtime coverage, the focused tariff suite and check-only quality gates pass, public compatibility and design coherence hold, and strict-TDD evidence is complete. The warnings are the proven pre-existing translation-directory check and coarse legacy whole-file coverage, not candidate-caused behavioral failures.
