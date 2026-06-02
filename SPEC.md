# PROJECT.md Specification

**Version:** `0.3` (draft)
**Status:** Breaking changes possible until `1.0`
**License:** Apache-2.0

PROJECT.md is a Markdown file with a YAML frontmatter block that describes a multi-agent pipeline. An orchestrator reads the file and executes it.

The spec is split into two layers:

- **Core** — the minimum every conformant orchestrator MUST support.
- **Extensions** — optional features. An orchestrator MAY support any subset.

This document uses RFC 2119 keywords (MUST, SHOULD, MAY).

---

## 1. File

### 1.1 Naming

A PROJECT.md file MUST match one of:

```text
PROJECT.md
PROJECT-<id>.md         e.g. PROJECT-01.md, PROJECT-news.md
PROJECT_<id>.md         e.g. PROJECT_01.md, PROJECT_news.md
```

Multiple files MAY coexist in one directory. An orchestrator MUST treat each file as an independent project.

### 1.2 Structure

A file consists of:

1. A YAML **frontmatter** block delimited by `---` (required).
2. A Markdown **body** with named `##` sections.

```markdown
---
spec_version: 0.3
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
| `spec_version` | string | yes      | Spec version this file targets. `0.3` for this version.                  |
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

To claim "PROJECT.md `0.3` Core compatible", an orchestrator MUST:

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

### 3.12 `ext:hosts` — agent placement

Adds a top-level `## Hosts` section declaring named execution targets, and a `host:` field on agents selecting one (or several) of them.

```markdown
## Hosts
- gpu_box:     ssh://ml@10.0.0.5
- gpu_backup:  ssh://ml@10.0.0.6
- scraper:     ssh://bot@worker-02.local
- local:       local

### collector
wave: 1
host: scraper

### trainer
wave: 2
host: [gpu_box, gpu_backup, local]
```

Rules:

- Each `## Hosts` entry is `name: target`. The `name` MUST match `[a-z][a-z0-9_]*` and is what `host:` on an agent references.
- The `target` is a free-form string interpreted by the orchestrator. Recommended schemes: `local`, `ssh://user@host[:port]`, `http(s)://...`, or a bare hostname/IP.
- An agent's `host:` is either a single name or a list of names. All referenced names MUST be declared in `## Hosts` (or be the literal `local`). Unknown names MUST cause the orchestrator to stop before the first agent runs.
- When `host:` is a list, the orchestrator MUST treat it as an ordered failover preference: try the first host; if it is unreachable or the agent fails to start there, try the next; and so on. The agent runs on at most one host per attempt. If every host in the list is exhausted, the agent is considered failed (and `ext:reliability` policies, if any, then apply).
- Failover applies to host-level failures (unreachable, refused, timed out before start). A successful agent run on host N is final — the orchestrator MUST NOT silently re-run it on host N+1 just because the agent's output was unsatisfactory; that is the job of `ext:reliability` / `ext:control-flow`.
- If `host:` is omitted, the agent runs on the orchestrator's default host (implementation-defined, typically `local`).
- Credentials for reaching a host MUST NOT be embedded as literals; use `ext:secrets` references (e.g. `ssh://ml@10.0.0.5?key={{ DEPLOY_KEY }}`). Resolution and transport are orchestrator-defined.
- Passing outputs between agents on different hosts MUST be transparent to agents — the orchestrator is responsible for transferring data across waves regardless of placement.
- `ext:constraints` fields (`allowed_paths`, `allowed_domains`) apply on the host where the agent actually runs.

### 3.13 `ext:status` — lifecycle state

Adds `status` to the frontmatter. Defined values: `active`, `paused`, `draft`. Orchestrators MUST skip files where `status != active`.

### 3.14 `ext:subagents` — hierarchy and dynamic sub-calls

Allows agents to invoke other agents ad-hoc, outside the static wave graph.

Adds:

- `spawnable: true` on an agent — marks it callable from another agent in addition to (or instead of) its `wave` slot.
- `may_call:` on an agent — explicit allowlist of agent names this agent is permitted to invoke.
- A top-level `## Subagents` block MAY redeclare or document the call graph for readability.
- `max_depth` on the frontmatter — maximum nesting depth for sub-calls (default: orchestrator-defined; recommended `3`).

```markdown
---
spec_version: 0.3
id: PROJECT-research
name: Research
max_depth: 3
---

### planner
wave: 1
may_call: [searcher, summarizer]

### searcher
spawnable: true
provider: anthropic
model: claude-haiku-4-5

### summarizer
spawnable: true
```

Rules:

- An agent MUST NOT invoke an agent not listed in its `may_call`. If `may_call` is omitted, the agent MAY NOT spawn anyone.
- An agent that is `spawnable: true` MAY omit `wave`. If both are present, the orchestrator MUST honor `wave` for static execution and additionally permit ad-hoc invocation.
- The orchestrator MUST stop the run with an error if invocation depth exceeds `max_depth`.
- Cycles in `may_call` are permitted but MUST be cut off by `max_depth`.

### 3.15 `ext:rag` — knowledge sources

Adds a top-level `## Knowledge` section describing retrieval sources, and a `knowledge:` field on agents selecting a subset.

```markdown
## Knowledge
- pharma_papers:
    type: rag
    source: ./vendor/pharma/
    embed_model: text-embedding-3-large
- web_cache:
    type: rag
    source: surrealdb://localhost:8000/web

### researcher
wave: 1
knowledge: [pharma_papers, web_cache]
```

Rules:

- Each entry has a `name` matching `[a-z][a-z0-9_]*` and a body with at least `type` and `source`.
- `type` values defined by this spec: `rag`. Orchestrators MAY recognize additional types.
- `source` is a free-form URI or path; resolution is orchestrator-defined.
- Knowledge is supplied to the agent as retrieval context, not as a tool call. An agent MUST NOT need to declare a tool to use its knowledge sources.
- Unknown knowledge names referenced from an agent MUST cause the orchestrator to stop before the first agent runs.

### 3.16 `ext:plugins` — first-class plugin manifests

Refines `ext:tools` by allowing tools to be declared as objects with versioning, source, and required capabilities, and by adding an optional `## Plugins` registry.

```markdown
## Plugins
registry: ./examples/

## Tools
- web_search
- id: pubmed
  version: ">=0.3"
  source: ./examples/wasm-plugin-pubmed
  requires: [http]
- id: store
  version: "1.x"
  source: registry:store
  requires: [surrealdb]
```

Rules:

- A tool entry MAY be either a string (as in `ext:tools`) or an object with `id` (required), and optional `version`, `source`, `requires`.
- `requires` lists capability names. The orchestrator MUST refuse to start the run if any required capability is unavailable.
- `version` is a semver range string. Resolution and execution sandbox (e.g. WASM) are orchestrator-defined.
- `## Plugins.registry` is a path or URI used to resolve `source: registry:<id>` references.

### 3.17 `ext:profiles` — profile inheritance

Adds `profile` and `profile_overlay` to the frontmatter. A profile is an external file describing default `provider`, `model`, `tools`, `secrets`, `constraints`, etc.

```markdown
---
spec_version: 0.3
id: PROJECT-pharma
name: Pharma scout
profile: pharma-scouting
profile_overlay: dev
---
```

Rules:

- The orchestrator MUST first load `profile`, then apply `profile_overlay` on top, then apply the PROJECT.md frontmatter and sections. Later layers override earlier ones field-by-field.
- Profile resolution (lookup path, format) is orchestrator-defined.
- An unresolved `profile` or `profile_overlay` MUST cause the orchestrator to stop before the first agent runs.
- A PROJECT.md MUST remain valid when its referenced profiles are absent in another orchestrator — i.e. profiles supply defaults, not required fields. (If a Core field is provided only by the profile, that orchestrator MUST report a clear error.)

### 3.18 `ext:eval` — project-level evaluation

Adds a top-level `## Evaluation` section describing project-wide success criteria, complementing per-agent `## Quality Checks` from `ext:reliability`.

```markdown
## Evaluation
- dataset: ./evals/hotpotqa.toml
  metric: f1
  threshold: 0.65
  on_fail: stop
- dataset: ./evals/regression.jsonl
  metric: exact_match
  threshold: 0.90
  on_fail: notify
```

Rules:

- Each entry MUST have `dataset`, `metric`, `threshold`. `on_fail` defaults to `stop`. Allowed `on_fail` values: `stop`, `notify`, `continue`.
- Evaluation runs after the last wave completes (and in `dry_run`/`plan` modes if the orchestrator supports replay).
- Metric names are orchestrator-defined; the spec does not enumerate them.

### 3.19 `ext:budget` — granular budgets (extends `ext:constraints`)

Adds finer-grained budget fields beyond `max_cost`:

| Field             | Scope                | Description                                         |
| ----------------- | -------------------- | --------------------------------------------------- |
| `max_cost`        | run / wave / agent   | Currency budget, e.g. `0.10 USD`.                   |
| `max_tokens_in`   | run / wave / agent   | Maximum input tokens.                               |
| `max_tokens_out`  | run / wave / agent   | Maximum output tokens.                              |
| `max_wall_time`   | run / wave / agent   | Wall-clock budget, e.g. `30m`, `2h`.                |
| `on_overrun`      | run / wave / agent   | `stop` (default), `degrade_model`, `notify`.        |

```markdown
---
spec_version: 0.3
id: PROJECT-01
name: Daily news
max_cost: 1.00 USD
max_wall_time: 30m
on_overrun: stop
---

### writer
wave: 2
max_cost: 0.10 USD
max_tokens_out: 4000
on_overrun: degrade_model
```

Rules:

- Tighter scope wins. Per-agent budget MUST NOT exceed the run-level budget; if it does, the orchestrator MUST stop before the first agent runs.
- `degrade_model` requires a `fallback` model to be declared (see `ext:cost-routing`); without one, the orchestrator MUST treat it as `stop`.

### 3.20 `ext:streaming` — incremental output between waves

Allows downstream agents to begin processing before upstream agents finish.

```markdown
### producer
wave: 1
streaming: true

### consumer
wave: 2
after: producer
consumes_stream: producer
```

Rules:

- An agent with `streaming: true` MUST emit output as a sequence of chunks. Chunk format is orchestrator-defined.
- A consumer with `consumes_stream: <name>` MAY be started by the orchestrator before its producer completes; the wave barrier is relaxed for this pair.
- A consumer without `consumes_stream` MUST still observe the wave barrier even if the producer is `streaming: true`.

### 3.21 `ext:checkpoints` — checkpointing and resume

Adds checkpoint and resume semantics for long or expensive runs.

Adds:

- `checkpoint` on the frontmatter or per agent. Values: `after_wave`, `after_agent`, `none` (default).
- `idempotency_key` on an agent — a stable string (may use `{{ ... }}`) identifying a unit of work; agents with a matching key in a previous successful run MUST NOT be re-executed on resume.
- A `resume_from: <run_id>` flag at run invocation (CLI/API surface, not file content) — orchestrator-defined.

```markdown
---
spec_version: 0.3
id: PROJECT-research
name: Research
checkpoint: after_wave
---

### expensive_call
wave: 2
idempotency_key: "search:{{ topic }}"
```

Rules:

- The orchestrator MUST persist enough state at each declared checkpoint to resume execution from that point.
- On resume, agents whose `idempotency_key` matches a successful prior result MUST be skipped and their cached output reused.
- Idempotency keys MUST be deterministic given the same frontmatter and inputs.

### 3.22 `ext:observability` — telemetry and tracing

Adds a `## Observability` section and `trace_tags` on agents.

```markdown
## Observability
tracing: langfuse
run_id_format: "{{ id }}-{{ timestamp }}"
log_level: info

### writer
wave: 2
trace_tags: [pharma, prod]
```

Rules:

- `tracing` is a free-form identifier (e.g. `langfuse`, `otel`, `none`). Backend wiring is orchestrator-defined.
- `run_id_format` MUST resolve to a unique string per run. `{{ timestamp }}` is provided by the orchestrator.
- `log_level` values: `debug`, `info`, `warn`, `error`. Default `info`.
- `trace_tags` are propagated to all spans emitted by the agent.

### 3.23 `ext:human-in-the-loop` — human review steps

Allows an agent step to pause for human approval.

```markdown
### approver
wave: 3
human_review: true
prompt_to_human: "Approve publication?"
on_reject:
  back_to: writer
on_approve:
  continue: true
timeout: 24h
```

Rules:

- An agent with `human_review: true` MUST pause after producing output and present `prompt_to_human` plus the agent's output to a human via an orchestrator-defined channel.
- `on_approve` and `on_reject` mirror the loop semantics of `ext:control-flow`. `on_reject.back_to` MUST reference an existing agent in an earlier wave.
- `timeout` (reusing `ext:reliability`) defines how long to wait for a decision; on timeout, the orchestrator MUST treat the step as failed and apply `## On Failure`.
- Without an interactive surface, an orchestrator MAY treat `human_review: true` as auto-reject; it MUST document this behavior.

### 3.24 `ext:cost-routing` — model selection by cost/quality

Generalizes `ext:models` to allow primary/fallback model configurations.

```markdown
### writer
wave: 2
model:
  primary: claude-opus-4
  fallback: claude-haiku-4-5
  policy: cost_aware    # or quality_first
```

Rules:

- `model` MAY be either a string (as in `ext:models`) or an object with `primary` (required), `fallback` (optional), `policy` (optional, default `quality_first`).
- Policies defined by this spec: `quality_first` (always use `primary` unless unavailable), `cost_aware` (orchestrator MAY use `fallback` when budget pressure or task class allows). Orchestrators MAY define additional policies.
- `fallback` is also used by `ext:budget`'s `on_overrun: degrade_model`.

### 3.25 `ext:i18n` — multi-language strings

Allows selected string fields to carry multiple language variants.

Eligible fields: `name` (frontmatter), `prompt_to_human` (`ext:human-in-the-loop`), agent instruction body.

```markdown
---
spec_version: 0.3
id: PROJECT-pharma
name:
  en: "Pharma scout"
  ru: "Фарма-скаут"
default_lang: en
---

### writer
wave: 1

::: lang en
Write a brief in English.
:::
::: lang ru
Напиши краткое описание на русском.
:::
```

Rules:

- A string field MAY be either a string or a map of language codes (BCP-47) to strings.
- The orchestrator MUST select a variant by frontmatter `default_lang`, falling back to `en`, and finally to the first defined language.
- For agent bodies, `::: lang <code>` ... `:::` blocks delimit per-language sections; the orchestrator MUST select one before substitution.

### 3.26 `ext:contracts` — paired input/output contracts

Strengthens `ext:io-schema` by declaring the consumer's expectations.

Adds `input_schema` on agents. When both `output_schema` (producer) and `input_schema` (consumer) are present and the consumer's `after` references the producer, the orchestrator MUST verify that the producer's schema satisfies the consumer's schema before the run starts.

```markdown
### writer
wave: 1
output_schema: ./schemas/article.json

### reviewer
wave: 2
after: writer
input_schema: ./schemas/article.json
```

Rules:

- Schema compatibility is checked statically (structural compatibility) at load time. The orchestrator MUST stop before any agent runs if the contract is violated.
- At runtime, `output_schema` validation continues to apply per `ext:io-schema`. `input_schema` MAY additionally be validated when the consumer starts.

### 3.27 `ext:prompt-templates` — external prompt files

Allows an agent's instruction body to be loaded from an external file, with variable substitution.

```markdown
### writer
wave: 1
prompt: ./prompts/p200.md
prompt_vars:
  topic: "{{ topic }}"
  tone: "neutral"
```

Rules:

- If `prompt` is set, the orchestrator MUST load the referenced file and use its contents as the agent's instruction body. The inline body, if any, MUST be ignored.
- `prompt_vars` are merged with frontmatter fields for `{{ ... }}` substitution; on conflict, `prompt_vars` win.
- Path resolution is relative to the PROJECT.md file. URLs are orchestrator-defined.

### 3.28 `ext:dry-run-replay` — replay against fixtures

Extends `ext:run-modes`. When `run_mode: dry_run`, the orchestrator MAY replay agents against recorded fixtures instead of calling LLMs.

```markdown
---
spec_version: 0.3
id: PROJECT-news
name: News
run_mode: dry_run
fixtures: ./fixtures/run-2026-05-30/
---
```

Rules:

- `fixtures` is a path/URI to recorded run outputs. Layout is orchestrator-defined; a recommended layout is `<fixtures>/<agent_name>.json`.
- When a fixture is present for an agent, the orchestrator MUST use it instead of invoking the model and MUST NOT incur cost for that agent.
- When a fixture is missing, the orchestrator MUST fail the agent (no silent fallback to live calls in `dry_run`).
- `ext:eval` MAY run against replayed outputs.

---

## 4. What this format is NOT

- Not a programming language. No conditionals beyond `loop.if`, no expressions, no functions.
- Not a replacement for orchestrator code. The orchestrator still implements the execution engine.
- Not a single-agent prompt file. Use AGENTS.md for that.
- Not tied to any model provider, framework, or runtime.

### 4.1 Conditional logic boundary (normative)

Conditional logic in a PROJECT.md file is permitted **only** in two places:

1. `loop.if` (`ext:control-flow`) — controlling re-execution of an existing agent.
2. `## On Failure` (`ext:reliability`) — reacting to an agent's failure.

Any other runtime-data-driven decision that would change **which** agents run, **in what order**, or **whether** an agent runs is out of scope for this spec. Specifically:

- A PROJECT.md MUST NOT introduce fields like `skip_if`, `run_if`, `enabled_if`, `branch_on`, dynamic `wave` selection, or runtime-computed `after`.
- The set of agents and the wave graph MUST be statically determinable from the file alone, before any agent runs.
- Logic that depends on agent output ("if the article is in English, skip translation"; "if no results, try a different source") MUST live **inside an agent's prompt**, not in the file structure. The agent decides and produces output; downstream agents adapt via their prompts.

Rationale: the wave graph is the auditable contract of the project. Once runtime data can reshape it, PROJECT.md becomes a programming language and loses its review, plan, and replay properties.

Orchestrators MUST reject unknown agent inline fields whose names suggest conditional gating of execution (e.g. `skip_if`, `run_if`, `enabled_if`) rather than silently ignoring them, even though section 2.5 otherwise mandates ignoring unknown fields. This is a deliberate exception to forward compatibility for this class of fields.

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
- Further refinement of streaming/async-wave semantics (`ext:streaming`) toward Core.
