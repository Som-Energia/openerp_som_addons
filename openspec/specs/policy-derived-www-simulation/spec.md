# Policy-Derived WWW Simulation Specification

## Purpose

Specify policy-derived WWW simulation behavior.

## Requirements

### Requirement: Policy-derived public operation

The system MUST expose `get_simulation_by_polissa_www`, accepting required `polissa_id` and optional `with_taxes` and `context`. When omitted, `with_taxes` and `context` MUST each default to `None`. Complete policies MUST be accepted regardless of lifecycle state. Results and exceptions MUST match `get_simulation_www` supplied with equivalent inputs.

#### Scenario: Equivalent policy simulation

- GIVEN a complete policy in any state and equivalent direct inputs
- WHEN both operations receive the same tax and context values
- THEN they return equal results or raise the same calculation exception

#### Scenario: Existing public contract is preserved

- GIVEN an existing valid or invalid `get_simulation_www` request
- WHEN it is introduced
- THEN `get_simulation_www` MUST retain its signature, defaults, results, and exception semantics

#### Scenario: Optional simulation values are omitted

- GIVEN a complete policy and a request containing only `polissa_id`
- WHEN `get_simulation_by_polissa_www` is called without `with_taxes` or `context`
- THEN both values default to `None` and are forwarded unchanged to policy lookup and the shared simulation core

### Requirement: Policy structural eligibility

The operation MUST require a real policy, tariff, CUPS, CUPS municipality, municipality subsystem, CNAE, invoicing selector, and non-empty powers with a period name and numeric kW value per entry. Incompleteness MUST raise a dedicated incomplete-policy domain exception before simulation. A missing fiscal position MUST remain valid.

#### Scenario: Required structure is missing

- GIVEN any required structure is absent or a power entry is incomplete
- WHEN the policy-derived operation is called
- THEN the dedicated incomplete-policy domain exception is raised before calculation

#### Scenario: Fiscal position is absent

- GIVEN an otherwise complete policy without a fiscal position
- WHEN the policy-derived operation is called
- THEN simulation proceeds with automatic fiscal classification

### Requirement: Selector and power mapping

The operation MUST map `atr` to `periods` and `index` to `index`. Present PVPC, flat-rate, unknown, and custom modes MUST raise `InvalidSimulationPricelist`. Period names MUST be lowercased and kW values converted to W.

#### Scenario: Supported selectors are mapped

- GIVEN complete policies using `atr` and `index`
- WHEN each policy-derived simulation is requested
- THEN the simulation selectors are respectively `periods` and `index`

#### Scenario: Unsupported selector is distinguished from absence

- GIVEN a complete policy with a present PVPC, flat-rate, unknown, or custom mode
- WHEN the policy-derived operation is called
- THEN `InvalidSimulationPricelist` is raised, not the incomplete-policy exception

#### Scenario: Powers are normalized

- GIVEN complete mixed-case powers expressed in kW
- WHEN policy inputs are derived
- THEN keys are lowercase and values equal kW multiplied by 1000

#### Scenario: Power range behavior

- GIVEN complete powers with maximum at, below, or above the inclusive 1–100 kW range
- WHEN simulation is requested
- THEN endpoints retain existing behavior; outside values raise `InvalidSimulationPowers`, not the incomplete-policy exception

### Requirement: Location and fiscal classification

The operation MUST use the CUPS municipality and preserve an explicit fiscal position. Without one, `home` MUST be true only for CNAE `9820` and maximum power strictly below 10 kW. Titular identity and VAT MUST NOT affect classification.

#### Scenario: Explicit fiscal position and supply location

- GIVEN an explicit fiscal position and CUPS municipality
- WHEN simulation inputs are derived
- THEN both values are used unchanged

#### Scenario: Domestic classification

- GIVEN no fiscal position, CNAE `9820`, and maximum power below 10 kW
- WHEN inputs are derived with any titular or VAT
- THEN `home` is true

#### Scenario: Industrial classification boundaries

- GIVEN no fiscal position and CNAE `9820` at 10 kW or another CNAE
- WHEN inputs are derived with any titular or VAT
- THEN `home` is false

### Requirement: Tax and context passthrough

The operation MUST pass `with_taxes` and `context` unchanged. Explicit, absent, and `None` context dates MUST retain `get_simulation_www` date and month-length semantics.

#### Scenario: Explicit date and taxes are preserved

- GIVEN a tax value and explicit simulation date
- WHEN policy-derived simulation is requested
- THEN taxation, tariff date, and month length match an equivalent direct request

#### Scenario: No date is supplied

- GIVEN `context` is `None` or has no date
- WHEN policy-derived simulation is requested
- THEN existing current-date fallback semantics apply unchanged
