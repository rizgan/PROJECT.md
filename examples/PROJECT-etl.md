---
spec_version: 0.5
id: PROJECT-etl
name: ETL Data Quality Pipeline
status: active
schedule: "0 8 * * *"
run_mode: production
language: [en]
output: [warehouse, slack]
max_cost: 1.00 USD
allowed_domains:
  - data.vendor.example.com
  - warehouse.example.com
  - hooks.slack.com
allowed_paths:
  - /output/{{ id }}/
---

## Sources
- https://data.vendor.example.com/api/v1/orders?date=today
- https://data.vendor.example.com/api/v1/customers?date=today

## Tools
- http_client
- warehouse_loader
- slack_webhook

## Secrets
DATA_API_KEY:   env:DATA_API_KEY
WAREHOUSE_DSN:  env:WAREHOUSE_DSN
SLACK_WEBHOOK:  env:SLACK_WEBHOOK

## Memory
- last_successful_extract_at: timestamp
- last_loaded_batch_id: string

## Agents

### extractor
wave: 1
provider: anthropic
model: claude-haiku-4-5
timeout: 2m
tools: [http_client]
output_schema: ./schemas/raw_batch.json

Extract today's order and customer records from Sources. Only include rows updated
after {{ memory.last_successful_extract_at }}.

### normalizer
wave: 2
after: extractor
provider: openai
model: gpt-4o
timeout: 3m
output_schema: ./schemas/normalized_batch.json

Normalize field names, types, and timezones to the canonical warehouse schema.

### dq_checker
wave: 2
after: extractor
provider: anthropic
model: claude-sonnet-4-6
timeout: 4m
output_schema: ./schemas/dq_report.json

Validate completeness, null rates, duplicate keys, and referential integrity.
Return blocking issues and warnings.

### loader
wave: 3
after: [normalizer, dq_checker]
provider: anthropic
model: claude-haiku-4-5
tools: [warehouse_loader]

If dq_checker reports no blocking issues, load normalized data to {{ output }}
using {{ WAREHOUSE_DSN }}.

### notifier
wave: 4
after: [loader, dq_checker]
provider: anthropic
model: claude-haiku-4-5
tools: [slack_webhook]

Send a run summary with row counts, failed checks, and load status to Slack.

## Quality Checks
- extractor: minimum 1 batch
- dq_checker: status is passed or warning
- loader: status is loaded or skipped

## On Failure
- extractor: retry after 30s, max 3 attempts
- loader: fallback save to /output/{{ id }}/ and notify

## Constraints
- agent: loader
  may: [write]
- agent: "*"
  may_not: [delete, purchase]

## Hooks
on_complete: https://hooks.example.com/done
on_error:    slack:#data-alerts
