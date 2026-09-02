# Proposal: Add Simulation by Policy for WWW

## Intent

Allow webforms consumers to request the existing electricity-cost simulation from a policy ID, avoiding duplicated and inconsistent policy-to-simulation mappings while preserving the established `get_simulation_www` API and economics.

## Scope

### In Scope
- Add `get_simulation_by_polissa_www(self, cursor, uid, polissa_id, with_taxes, context)` for policies in any lifecycle state when required structural data is complete.
- Derive tariff, CUPS municipality, powers, invoicing selector, fiscal position, and Canary housing classification; pass `with_taxes` and `context` unchanged.
- Fail fast with an explicit domain exception for missing policy structure; keep missing `fiscal_position_id` valid.
- Refactor both public methods onto a behavior-preserving private calculation core, using strict RED-GREEN-REFACTOR tests.

### Out of Scope
- Extending simulation economics to PVPC, flat-rate, unknown, or custom invoicing modes.
- Fixing unrelated legacy helpers, including contradictory fiscal-classification helpers.
- Repairing or migrating incomplete policy records.

## Capabilities

### New Capabilities
- `policy-derived-www-simulation`: Derive and validate simulation inputs from a policy, map `atr` to `periods` and `index` to `index`, reject unsupported modes with `InvalidSimulationPricelist`, and preserve existing simulation outcomes.

### Modified Capabilities
- None; no existing main OpenSpec capabilities are present, and `get_simulation_www` behavior remains unchanged.

## Approach

Validate the policy, tariff, CUPS, municipality, subsystem, CNAE, supported mode, and complete period powers before calculation. Convert kW powers to watts and period names to lowercase. Preserve an explicit fiscal position; otherwise set `home` only when CNAE is `9820` and maximum power is strictly below 10 kW. Move the current calculation mechanically into a private core called by thin public adapters.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `som_webforms_helpers/giscedata_polissa_tarifa.py` | Modified | New adapter, validation, mapping, and shared core |
| `som_webforms_helpers/exceptions/som_webforms_exceptions.py` | Modified | Explicit incomplete-policy domain exception |
| `som_webforms_helpers/tests/test_tarifes.py` | Modified | RED-first mapping, boundary, failure, and regression coverage |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Refactor changes legacy results or exceptions | Med | Retain existing tests and add equivalence coverage |
| Wrong IGIC classification at 10 kW | Med | Test `< 10` domestic and exactly 10 industrial |

## Rollback Plan

Revert the adapter, exception, tests, and core extraction together, restoring the original `get_simulation_www` body and signature.

## Dependencies

- Existing OpenERP policy model and simulation coefficient, consumption, average-price, tariff-price, and fiscal-position configuration.

## Success Criteria

- [ ] Complete `atr` and `index` policies produce the same result as equivalent `get_simulation_www` calls.
- [ ] Every required structural-data omission fails through the explicit domain exception before calculation.
- [ ] Unsupported modes raise `InvalidSimulationPricelist`; all existing simulation tests remain green.
