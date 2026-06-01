---
spec_version: 0.1
id: PROJECT-01
name: Tech News Daily
status: active
schedule: "0 8 * * *"
run_mode: production
language: [en, ku, ka, ru, zh]
output: [wordpress, telegram]
max_cost: 1.00 USD
allowed_domains:
  - api.unsplash.com
  - wordpress.example.com
  - api.telegram.org
allowed_paths:
  - /output/{{ id }}/
---

## Sources
- https://techcrunch.com/feed
- https://theverge.com/rss

## Tools
- web_search
- unsplash_api
- wordpress_api
- telegram_bot

## Secrets
WORDPRESS_KEY:  env:WP_API_KEY
TELEGRAM_TOKEN: env:TG_BOT_TOKEN
UNSPLASH_KEY:   file:.env

## Memory
- published_urls: set
- last_run_timestamp: timestamp

## Agents

### collector
wave: 1
provider: anthropic
model: claude-haiku-4-5
timeout: 2m
tools: [web_search]
output_schema: ./schemas/story.json

Collect 5 most important stories from Sources published after
{{ memory.last_run_timestamp }}. Skip URLs in {{ memory.published_urls }}.

### translator
wave: 2
after: collector
provider: anthropic
model: claude-sonnet-4-6
timeout: 5m

Translate each story into: {{ language }}.

### image_finder
wave: 2
after: collector
provider: openai
model: gpt-4o
timeout: 3m
tools: [web_search, unsplash_api]

Find a free-to-use image for each story, minimum 1200px wide.

### publisher
wave: 3
after: [translator, image_finder]
provider: anthropic
model: claude-haiku-4-5
tools: [wordpress_api, telegram_bot]

Publish to {{ output }} using {{ WORDPRESS_KEY }} and {{ TELEGRAM_TOKEN }}.

## Quality Checks
- collector: minimum 3 items, not older than 24 hours
- publisher: status is published or HTTP 200

## On Failure
- collector: retry after 30s, max 3 attempts
- publisher: fallback save to /output/{{ id }}/ and notify

## Constraints
- agent: publisher
  may: [publish]
- agent: "*"
  may_not: [delete, purchase]

## Hooks
on_complete: https://hooks.example.com/done
on_error:    telegram:@mychannel
