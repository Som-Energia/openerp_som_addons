---
name: pr-token-cost-logger
description: "Trigger: PR token usage, AI cost, model metrics, token report. Calculate and format verified OpenCode token usage and estimated costs for pull requests."
license: Apache-2.0
metadata:
  author: oriol
  version: "1.1"
---

## Activation Contract

Use when asked to calculate, record, format, or comment on AI token usage or costs for a pull request.

## Hard Rules

- Use only usage values from OpenCode session/message metadata, an exported usage report, or values supplied by the user. Never infer token counts from text length.
- Identify the provider and exact model for each usage row. Keep different models separate before totaling.
- Prefer provider-reported cost, label it as reported, and distinguish it from OpenCode's recorded cost and any estimate. Do not treat an OpenCode cost of zero as proof of a zero invoice.
- Before estimating, load `references/rates-and-impact-factors.md`. Use only an exact model/rate match whose source and effective date are known; if rates may be stale or the model is unmapped, ask or mark cost unavailable.
- Keep uncached input, cache-read input, cache-write input, output, and reasoning distinct. Apply a cache rate only to cache tokens not already included in the input count. Apply output rates to reasoning only when the usage/provider semantics confirm reasoning is billable as output. If any nonzero category has no rate, mark the cost incomplete instead of presenting a full total.
- Treat credit conversion, energy, CO₂, and cooling-water results as estimates. State their source, date, units, and assumptions; never present them as metered consumption or verified emissions.
- Do not publish a comment unless the user explicitly requested publication and the repository and PR are unambiguous. Never include prompts, completions, or secrets in the report.

## Decision Gates

| Available evidence | Action |
|---|---|
| Token counts are unavailable or ambiguous | Ask for the session/export or report usage as unavailable; do not estimate counts. |
| Counts exist but applicable rates are missing, stale, or unmapped | Report counts only and mark cost unavailable; ask for current rates if needed. |
| Provider-reported cost exists | Prefer it and label it reported; show any CodeBurn/local estimate separately. |
| Nonzero token category has no matching rate | Report that category and mark the all-in cost incomplete; do not silently omit it. |
| Credit price or impact factors are supplied | Convert only using the dated reference assumptions; report credits, currency, energy, CO₂, and water as separate derived values. |
| User requests a PR comment with a clear target | Prepare the report, publish through an authorized integration, and verify success. Otherwise return draft Markdown only. |

## Execution Steps

1. Confirm the requested session/PR and collect usage by provider and exact model. Prefer per-message data when session aggregates combine models.
2. Load the dated rate reference; record the usage source, rate source, currency, and assumptions. Calculate each priced category separately per million tokens, then sum only if no nonzero category is unpriced.
3. If supported by the reference, calculate `EUR = credits * EUR_per_credit`, `kWh = generated_tokens / 1,000,000 * kWh_per_million_generated_tokens`, `CO2_kg = kWh * kg_CO2_per_kWh`, and `water_L = kWh * L_water_per_kWh`. Define which output/reasoning tokens count as generated.
4. Return a Markdown table with provider/model, input/cache/output/reasoning counts, total token convention, credits/cost and currency, energy, CO₂, water, sources, and estimate/report status. Include grand totals only for compatible units and complete data.
5. If publication was explicitly requested, confirm the target PR is unambiguous, post only the report, and state whether publication succeeded.

## Output Contract

Return a concise Markdown table by default, or JSON when requested. Mark unavailable/incomplete values explicitly; never present an estimate as an exact provider charge or environmental measurement. Include publication status when posting was requested.

## References

- Use OpenCode session usage metadata or a user-provided export as the usage source; do not assume a particular local file format.
- `references/rates-and-impact-factors.md` — dated, user-supplied model credit rates, credit conversion, and energy/environmental factors. Reconfirm when out of date.
