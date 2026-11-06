# Model rates and impact factors

**Effective date:** 2026-11-06
**Rate source:** User-provided pricing table and subscription figures. These are not provider invoices or independently verified tariffs. Confirm current values before using them for a later report.

## Model rates

All rates are **credits per 1,000,000 tokens**. “Input” means uncached input; apply the cache-input rate only to cache-read tokens reported separately and not already included in input. No cache-write rate was supplied.

| Model label | Input | Cache input | Output |
|---|---:|---:|---:|
| GPT-6.1 Sol | 50 | 2.5 | 250 |
| GPT-6.1 Terra | 25 | 1.25 | 125 |
| GPT-6 Astra | 250 | 25 | 1,250 |
| GPT-6 Astra Law * | 250 | 25 | 1,250 |
| GPT-6 Sol | 50 | 5 | 250 |
| GPT-6 Luna | 2.5 | 0.25 | 12.5 |
| GPT-5.6 Sol | 100 | 10 | 500 |
| GPT-5.6 Terra | 50 | 5 | 300 |
| GPT-5.6 Luna | 5 | 0.5 | 30 |
| GPT-6 Rosalind Research | 375 | 37.5 | 1,875 |
| GPT-5.5 Rosalind Research | 125 | 12.5 | 625 |
| GPT-5.5 Rosalind Discovery | 125 | 12.5 | 625 |
| Daybreak Blue (GPT-5.6 Sol) | 100 | 10 | 500 |
| Daybreak Red | 312.5 | 31.25 | 1,875 |
| GPT-5.3-Codex | 43.75 | 4.375 | 350 |
| GPT-5.2 | 43.75 | 4.375 | 350 |
| GPT-Image-2 (image) | 200 | 50 | 750 |
| GPT-Image-2 (text) | 125 | 31.25 | 250 |

Match the exact provider model to a label only when the mapping is known. Do not infer that two similarly named models or service routes have identical rates. If cache-write tokens are nonzero, report their count and mark the all-in credit estimate incomplete until a rate is supplied.

The source table marks GPT-6 Astra Law with an asterisk but did not provide its footnote; preserve the mark and do not infer additional pricing conditions.

## Credit-to-currency estimate

User-provided subscription basis: 25,000 credits/month and €8,000/year. Assuming the full annual allocation is used:

`EUR_per_credit = 8,000 / (25,000 * 12) = 0.0266667 EUR`

This is an amortized average subscription cost per credit, not a marginal or provider-reported token price. If fewer credits are used, the effective cost per consumed credit is higher. Keep credit totals available even when EUR conversion is shown.

## Energy and environmental estimates

User-provided factors, effective 2026-11-06:

- Energy: approximately `0.6 kWh` per 1,000,000 generated tokens.
- Emissions: `0.34 kg CO2` per kWh.
- Cooling water: `0.38 L` per kWh.

Derived per 1,000,000 generated tokens: approximately `0.6 kWh`, `0.204 kg CO2`, and `0.228 L` of cooling water. These are estimates, not metered usage or verified lifecycle emissions.

For OpenCode metadata that reports `output` and `reasoning` separately, count `output + reasoning` as generated tokens only if the provider's billing/usage semantics treat reasoning as output. If that is unclear, show both counts and request clarification rather than silently choosing one.
