---
name: pr-token-cost-logger
description: "Trigger: PR token usage, AI cost, model metrics, token report. Calculate and format verified OpenCode token usage and estimated costs for pull requests."
license: Apache-2.0
metadata:
  author: oriol
  version: "1.0"
---

## Activation Contract

Use when asked to calculate, record, format, or comment on AI token usage or costs for a pull request.

## Hard Rules

- Use only usage values from OpenCode session/message metadata, an exported usage report, or values supplied by the user. Never infer token counts from text length.
- Identify the provider and exact model for each usage row. Keep different models separate before totaling.
- Use a reported provider cost when available and label it as reported. Otherwise calculate an estimate only when the applicable input/output rates and their source are available. Never guess or silently reuse stale prices.
- Include cache or other separately priced token categories only when both usage and matching rates are available; avoid double-counting categories included in input/output totals.
- Do not publish a comment unless the user explicitly requested publication and the repository and PR are unambiguous. Never include prompts, completions, or secrets in the report.

## Decision Gates

| Available evidence | Action |
|---|---|
| Token counts are unavailable or ambiguous | Ask for the session/export or report usage as unavailable; do not estimate counts. |
| Counts exist but applicable rates do not | Report counts only and mark cost unavailable. |
| Provider-reported cost exists | Prefer it; distinguish it from any calculated estimate. |
| User requests a PR comment with a clear target | Prepare the report, publish through an authorized integration, and verify success. Otherwise return draft Markdown only. |

## Execution Steps

1. Confirm the requested session or usage data and collect input/output counts by provider and model.
2. Record the source of counts and, for estimates, the source and currency of each rate. Calculate `input_tokens / 1,000,000 * input_rate + output_tokens / 1,000,000 * output_rate`.
3. Present a Markdown report with model, input tokens, output tokens, total tokens, cost, and whether cost is reported or estimated. Include a grand total only when the currency and included data are consistent.
4. If publication was explicitly requested, confirm the target PR is unambiguous, post only the report, and state whether publication succeeded.

## Output Contract

Return a concise Markdown table by default, or JSON when requested. Mark unavailable values explicitly; never present a partial or estimated cost as an exact provider charge. Include publication status when posting was requested.

## References

- Use OpenCode session usage metadata or a user-provided export as the usage source; do not assume a particular local file format.
