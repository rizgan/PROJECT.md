# PROJECT.md Specification

**Version:** `0.1` (draft)
**Status:** Breaking changes possible until `1.0`
**License:** MIT

PROJECT.md is a Markdown file with a YAML frontmatter block that describes a multi-agent pipeline. An orchestrator reads the file and executes it.

The spec is split into two layers:

- **Core** — the minimum every conformant orchestrator MUST support.
- **Extensions** — optional features. An orchestrator MAY support any subset.

This document uses RFC 2119 keywords (MUST, SHOULD, MAY).

---

## 1. File

### 1.1 Naming

A PROJECT.md file MUST match one of:

```
PROJECT.md
PROJECT-<id>.md         e.g. PROJECT-01.md, PROJECT-news.md
```

Multiple files MAY coexist in one directory. An orchestrator MUST treat each file as an independent project.

### 1.2 Structure

A file consists of:

1. A YAML **frontmatter** block delimited by `---` (required).
2. A Markdown **body** with named `##` sections.

```markdown
---
spec_version: 0.1
id: PROJECT-01
name: My pipeline
---

## Agents

### agent_name
wave: 1
Instruction text for the agent.
```

### 1.3 Section names

Section names are case-insensitive and matched on the heading text (`## Agents`, `## agents`, `## AGENTS` are equivalent).

Unknown sections MUST be ignored by the orchestrator (forward compatibility).

---

## 2. Core

This section is normative. A "PROJECT.md compatible" orchestrator MUST implement all of section 2.

### 2.1 Frontmatter (Core)

| Field          | Type   | Required | Description                                                              |
| -------------- | ------ | -------- | ------------------------------------------------------------------------ |
| `spec_version` | string | yes      | Spec version this file targets. `0.1` for this version.                  |
| `id`           | string | yes      | Stable identifier. Allowed: `[A-Za-z0-9_-]+`.                            |
| `name`         | string | yes      | Human-readable name.                                                     |

### 2.2 `## Agents`

Required. Contains one or more `### <agent_name>` subsections.

Agent name MUST match `[a-z][a-z0-9_]*`.

Each agent subsection has two parts:

1. **Inline fields** — lines of `key: value` directly under the heading.
2. **Instruction body** — free-form Markdown after the inline fields. This is the agent's prompt.

```markdown
### writer
wave: 2
after: collector

Write a summary based on the collector output.
```

**Core inline fields:**

| Field   | Type              | Required | Description                                                                |
| ------- | ----------------- | -------- | -------------------------------------------------------------------------- |
| `wave`  | integer ≥ 1       | yes      | Execution wave. Agents with the same `wave` run in parallel.               |
| `after` | string or list    | no       | Names of agents whose output this agent consumes. Defaults to prior wave.  |

### 2.3 Execution model

- The orchestrator MUST execute waves in ascending numeric order.
- All agents in wave `N` MUST start only after every agent in wave `N-1` has completed.
- Agents in the same wave MUST be eligible to run in parallel.
- If `after` is specified, the orchestrator MUST pass the listed agents' outputs as input. If `after` is omitted, the orchestrator MUST pass outputs of all agents in the previous wave.

### 2.4 Template variables

The body of any agent MAY reference frontmatter fields via `{{ field_name }}`. The orchestrator MUST substitute these values before sending the instruction to the agent.

Substitution syntax: double curly braces, optional whitespace, dot-path for nested keys: `{{ foo }}`, `{{ foo.bar }}`. No expressions, no filters, no logic. (Extensions MAY add more.)

If a referenced variable is unresolved, the orchestrator MUST stop with an error before executing the first agent.

### 2.5 Conformance

To claim "PROJECT.md `0.1` Core compatible", an orchestrator MUST:

1. Parse files matching section 1.1.
2. Validate Core frontmatter (2.1).
3. Execute the `## Agents` section per section 2.3.
4. Perform variable substitution per section 2.4.
5. Reject files declaring a `spec_version` it does not support.
6. Ignore unknown sections, unknown frontmatter fields, and unknown agent inline fields (forward compatibility).

---

## 3. Extensions

This section is non-normative for Core conformance. Each extension is independent — an orchestrator MAY support any subset and MUST document which extensions it supports.

Each extension below has an identifier (e.g. `ext:tools`). An orchestrator advertising support uses this identifier.

### 3.1 `ext:io-schema` — typed agent I/O

Adds `output_schema` to agents. Value is a path or URL to a JSON Schema.

```markdown
### collector
wave: 1
output_schema: ./schemas/story.json
```

The orchestrator MUST validate the agent's output against the schema and treat a schema violation as agent failure.

### 3.2 `ext:models` — per-agent model selection

Adds `provider` and `model` fields to agents.

```markdown
### writer
wave: 2
provider: anthropic
model: claude-sonnet-4-6
```

Provider/model identifiers are free-form strings interpreted by the orchestrator.

### 3.3 `ext:tools` — agent tools

Adds a top-level `## Tools` section listing available tool identifiers, and a `tools:` field on agents selecting a subset.

```markdown
## Tools
- web_search
- wordpress_api

### publisher
wave: 3
tools: [wordpress_api]
```

### 3.4 `ext:secrets` — secret references

Adds a `## Secrets` section. Values MUST be references, never literals:

```markdown
## Secrets
WORDPRESS_KEY: env:WP_API_KEY
TELEGRAM_TOKEN: file:.env
DB_PASSWORD:   vault:secret/db#password
```

Reference schemes: `env:`, `file:`, `vault:`. Resolved secrets are available to agents as `{{ WORDPRESS_KEY }}`. The orchestrator MUST fail fast if any secret cannot be resolved before any agent runs.

### 3.5 `ext:control-flow` — loops

Adds a `loop:` block to agents:

```markdown
### judge
wave: 3
loop:
  if: status == "rejected"
  back_to: writer
  max_loops: 3
```

If the agent's output matches `if`, the orchestrator re-runs `back_to` and the subsequent waves, up to `max_loops` times.

The expression language for `if` is limited to: `<field> <op> <literal>` where `op ∈ {==, !=, >, <, >=, <=}`.

### 3.6 `ext:reliability` — timeouts, failure policy, quality checks

Adds:

- `timeout` field on agents (e.g. `30s`, `5m`).
- `## Quality Checks` — list of `agent: rule` assertions.
- `## On Failure` — list of `agent: action` policies. Actions: `retry`, `skip`, `stop`, `notify`, `fallback`.

```markdown
### collector
wave: 1
timeout: 2m

## Quality Checks
- collector: minimum 3 items

## On Failure
- collector: retry after 30s, max 3 attempts
```

### 3.7 `ext:constraints` — guardrails

Adds top-level fields:

| Field             | Description                                                    |
| ----------------- | -------------------------------------------------------------- |
| `max_cost`        | Hard budget for the entire run, e.g. `1.00 USD`.               |
| `allowed_domains` | List of domains agents MAY contact.                            |
| `allowed_paths`   | List of filesystem paths agents MAY write to.                  |

Adds top-level `## Constraints` section with per-agent action policies:

```markdown
## Constraints
- agent: publisher
  may: [publish]
- agent: "*"
  may_not: [delete, purchase]
```

The orchestrator MUST enforce constraints before executing each action and treat violations as agent failure.

### 3.8 `ext:memory` — cross-run state

Adds `## Memory` section declaring named keys that persist between runs:

```markdown
## Memory
- published_urls: set
- last_run_timestamp: timestamp
```

Available to agents as `{{ memory.<key> }}`. The orchestrator chooses the storage backend.

### 3.9 `ext:hooks` — lifecycle hooks

Adds a `## Hooks` section:

```markdown
## Hooks
on_start:    https://hooks.example.com/start
on_complete: https://hooks.example.com/done
on_error:    https://hooks.example.com/error
```

Each value is either an HTTP(S) URL (orchestrator POSTs a JSON event) or a notifier reference (e.g. `telegram:@channel`) defined by the orchestrator.

### 3.10 `ext:run-modes` — execution mode

Adds `run_mode` to the frontmatter. Defined values: `dry_run`, `test`, `production`. Semantics are orchestrator-defined.

### 3.11 `ext:scheduling` — recurring runs

Adds `schedule` to the frontmatter. Value is a cron expression.

### 3.12 `ext:status` — lifecycle state

Adds `status` to the frontmatter. Defined values: `active`, `paused`, `draft`. Orchestrators MUST skip files where `status != active`.

---

## 4. What this format is NOT

- Not a programming language. No conditionals beyond `loop.if`, no expressions, no functions.
- Not a replacement for orchestrator code. The orchestrator still implements the execution engine.
- Not a single-agent prompt file. Use AGENTS.md for that.
- Not tied to any model provider, framework, or runtime.

---

## 5. Versioning

This spec uses semver-like versioning at the spec level:

- `0.x` — draft, breaking changes possible.
- `1.x` — stable. Additions are non-breaking; field semantics will not change.
- A new major version MAY break compatibility.

Files MUST declare `spec_version`. Orchestrators MUST reject unsupported versions.

---

## 6. Open questions

Tracked as issues in the repository. Notable:

- Template language scope — should `{{ ... }}` support filters or stay literal-only?
- Agent-to-agent direct messaging — needed in Core or stays in Extensions?
- Streaming outputs between waves — out of scope for v0.1.
