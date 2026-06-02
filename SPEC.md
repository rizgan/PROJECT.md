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

| Field          | Type            | Required | Description                                                                   |
| -------------- | --------------- | -------- | ----------------------------------------------------------------------------- |
| `spec_version` | string          | yes      | Spec version this file targets. `0.3` for this version.                       |
| `id`           | string          | yes      | Stable identifier. Allowed: `[A-Za-z0-9_-]+`.                                 |
| `name`         | string          | yes      | Human-readable name.                                                          |
| `extensions`   | list of strings | no       | Extension identifiers (e.g. `ext:tools`) that this file relies on. See 2.1.1. |

#### 2.1.1 `extensions` declaration

A file MAY declare which extensions it relies on:

```yaml
extensions:
  - ext:tools
  - ext:secrets
  - ext:streaming
  - ext:checkpoints
```

Rules:

- Each entry MUST be an extension identifier defined in section 3 (e.g. `ext:tools`, `ext:io-schema`).
- An orchestrator that does not support an extension listed here MUST stop with a clear error before any agent runs ("file requires `ext:streaming`, this orchestrator does not support it"). This is fail-fast on declared dependencies.
- An orchestrator that supports an extension listed here MUST treat the corresponding fields/sections as active for this file.
- If `extensions` is omitted, the orchestrator MUST infer required extensions from the fields and sections present in the file. Inference failures (an unknown field that is not gated by 2.5(7)) follow the warning rule of 2.5(7).
- Listing an extension that the file does not actually use is permitted (no-op) but discouraged; a strict validator MAY warn.
- The `extensions` list is the file's **declared dependencies**. The orchestrator's **advertised support** (per the introduction to section 3) is the converse. A run is feasible iff `file.extensions ⊆ orchestrator.supported_extensions`.

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
6. Ignore unknown **sections** and unknown **frontmatter** fields (forward compatibility — new features land via new sections and new frontmatter keys).
7. Treat unknown **agent inline fields** as follows (agent inline fields are a hot zone where silent ignore is dangerous):
   - A field whose name matches the gating pattern `^(if|when|unless|cond|gate|predicate|only_when|skip|run_if|enabled)(_.*)?$` MUST cause the orchestrator to stop with an error. The pattern matches both bare names (`unless`, `gate`, `cond`, ...) and any suffixed variant (`skip_if`, `run_if_empty`, `gate_on_error`, ...). See section 4.1.
   - Any other unknown inline field SHOULD produce a warning. An orchestrator MAY accept it for forward compatibility, but MUST NOT assign it semantics it does not specify.

### 2.6 Variable namespaces

Core template substitution (2.4) resolves names against frontmatter fields. Extensions MAY introduce additional top-level namespaces in `{{ ns.key }}` form (e.g. `{{ memory.x }}` from `ext:memory`, `{{ timestamp }}` from `ext:observability`). An orchestrator MUST resolve namespaces only for extensions it supports; an unresolved namespace MUST be treated as an unresolved variable per 2.4.

Layered substitution sources, when multiple are active, are merged in the following precedence (later wins):

1. Frontmatter fields (Core).
2. Profile-supplied fields (`ext:profiles`), once resolved.
3. Memory namespace (`ext:memory`), under `memory.`.
4. Per-agent `prompt_vars` (`ext:prompt-templates`).

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

`max_loops` MUST be specified when `loop:` is present; there is no default. Omitting it is a load-time error. The minimum meaningful value is `1` (one re-run).

The expression language for `if` is limited to: `<field> <op> <literal>` where `op ∈ {==, !=, >, <, >=, <=}`. `<field>` resolves against the agent's output object (the agent whose `loop:` block this is). Extensions MAY contribute additional named fields to this scope (see e.g. `ext:human-in-the-loop`).

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

`paused` means "do not start new runs of this project". It is **not** related to `ext:checkpoints` resume — a paused project does not retain or consume checkpoint state by virtue of being paused, and resuming a previously checkpointed run is governed by `resume_from`, not by toggling `status`.

### 3.14 `ext:subagents` — hierarchy and dynamic sub-calls

Allows agents to invoke other agents ad-hoc, outside the static wave graph.

Adds:

- `spawnable: true` on an agent — marks it callable from another agent in addition to (or instead of) its `wave` slot.
- `may_call:` on an agent — explicit allowlist of agent names this agent is permitted to invoke.
- A top-level `## Subagents` block carrying execution policy for sub-calls. Defined keys:
  - `max_depth` (integer ≥ 1, default `3`) — maximum nesting depth for ad-hoc sub-calls. Cycles in `may_call` are permitted but MUST be cut off here.
  - `on_depth_exceeded` (`stop` | `notify`, default `stop`) — action when `max_depth` is hit.
  Orchestrators MUST ignore unknown keys inside `## Subagents` (forward compatibility).

```markdown
---
spec_version: 0.3
id: PROJECT-research
name: Research
---

## Subagents
max_depth: 3
on_depth_exceeded: stop

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
- When invocation depth exceeds `## Subagents.max_depth`, the orchestrator MUST apply `on_depth_exceeded`.

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

- The orchestrator MUST resolve `profile` and `profile_overlay` **before** validating Core fields (2.1). Layer order: `profile` first, then `profile_overlay`, then PROJECT.md frontmatter and sections. Later layers override earlier ones field-by-field.
- Profile resolution (lookup path, format) is orchestrator-defined.
- An unresolved `profile` or `profile_overlay` MUST cause the orchestrator to stop before the first agent runs.
- Profiles MAY supply Core-required fields (e.g. `name`) and extension fields (`provider`, `model`, `tools`, `secrets`, `constraints`, ...). A PROJECT.md whose Core validity depends on a profile is therefore **not portable** to an orchestrator that lacks that profile; the author SHOULD make this dependency explicit (e.g. encode the profile name in `id`, document it in the body) and the orchestrator MUST report a clear error rather than silently substituting defaults.

### 3.18 `ext:eval` — project-level evaluation

Adds a top-level `## Evaluation` section describing project-wide success criteria, complementing per-agent `## Quality Checks` from `ext:reliability`.

This extension covers **dataset-based** evaluation only. For assertions on a single agent's output without a dataset (e.g. "publisher must produce ≥ 5 items"), use `## Quality Checks` from `ext:reliability`.

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
- Relationship to `ext:constraints` (3.7): when both extensions are supported, `ext:budget` **supersedes** 3.7's `max_cost`. The 3.7 `max_cost` is equivalent to the run-scope `max_cost` of 3.19; the two MUST NOT contradict, and an orchestrator that supports both MUST treat them as the same field.
- `on_overrun: degrade_model` requires `ext:cost-routing` support and a declared `fallback` model on the affected agent. Without either, the orchestrator MUST treat `degrade_model` as `stop`.

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

This extension is an explicit, scoped relaxation of section 2.3. It applies **only** to a producer/consumer pair where the producer is `streaming: true` and the consumer declares `consumes_stream: <producer>`. For every other pair of agents, section 2.3's wave barrier remains in force.

Rules:

- An agent with `streaming: true` MUST emit output as a sequence of chunks. Chunk format is orchestrator-defined.
- A consumer with `consumes_stream: <name>` MAY be started by the orchestrator before its producer completes; the wave barrier is relaxed only for this pair.
- A consumer without `consumes_stream` MUST still observe the wave barrier even if the producer is `streaming: true`.
- `after:` semantics are extended for streaming pairs: the consumer receives a **partial input** stream rather than a final output. Handling partial input (buffering, validating, deciding when it has "enough") is the consumer's responsibility, not the orchestrator's. The producer's final output, when available, MUST also be delivered as the closing element of the stream.
- `ext:io-schema` validation against `output_schema` applies to the producer's final output, not to individual chunks.

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
- The orchestrator MUST retain successful agent outputs at least for the lifetime of a single `run_id` and any resume chain derived from it. Cross-run reuse (matching keys across independent `run_id`s) is **not specified** and is orchestrator-defined.
- On resume **within the same run_id chain**, agents whose `idempotency_key` matches a successful prior result MUST be skipped and their stored output reused.
- Idempotency keys MUST be deterministic given the same frontmatter and inputs.
- Interaction with `ext:hosts`: by default, resume MUST replay each agent on the same host where its checkpoint was produced. If that host is unreachable, the orchestrator MAY fail the resume, OR (if it documents this capability) replicate state to a fallback host listed in the agent's `host:` failover list. Silent migration to a different host is not permitted.
- Interaction with `ext:streaming`: a `streaming: true` producer's checkpoint is considered committed only after delivery of the final chunk (end-of-stream). A consumer with `consumes_stream:` MUST NOT be checkpointed at `after_agent` earlier than its producer; an `after_wave` checkpoint covering both is committed only when both have completed. On resume, the producer MUST be re-executed from scratch and the consumer MUST re-consume the resulting stream — partial-stream replay is not specified in v0.3. Orchestrators MAY buffer the full chunk sequence to enable mid-stream resume; if they do, this MUST be documented as an extension to this rule.

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

Allows an agent step to pause for human approval. Reuses the `loop:` syntax of `ext:control-flow` rather than introducing a parallel form.

```markdown
### approver
wave: 3
human_review: true
prompt_to_human: "Approve publication?"
timeout: 24h
loop:
  if: decision == "rejected"
  back_to: writer
  max_loops: 3
```

Rules:

- An agent with `human_review: true` MUST pause after producing output and present `prompt_to_human` plus the agent's output to a human via an orchestrator-defined channel. The human's decision is recorded as a field named `decision` (typical values `approved` / `rejected`) on the agent's output object; it is therefore accessible to `loop.if` per `ext:control-flow`'s expression scope (3.5), but it is not a new template namespace and does not appear in `{{ ... }}` substitution.
- Re-routing on rejection is expressed via the existing `loop:` block (`ext:control-flow`); no new `on_approve`/`on_reject` fields are introduced.
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
- For agent bodies, `::: lang <code>` ... `:::` blocks (Pandoc-style fenced divs) delimit per-language sections. The orchestrator MUST select exactly one block before applying `{{ ... }}` substitution; substitution rules (Core 2.4 and 2.6) apply unchanged inside the selected block.
- If an agent body contains `::: lang :::` blocks AND free text outside any block, the free text is treated as a `default` block usable as the final fallback. If no `::: lang :::` blocks are present, the entire body is the (single) default.
- If the chosen language has no matching block, the orchestrator MUST fall back in order: `default_lang` block → `en` block → the `default` (free-text) block, if any → the first defined block. If none of these exist, the orchestrator MUST stop with an error before the agent runs.

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

- Static compatibility is defined narrowly: every property listed as `required` by the consumer's `input_schema` MUST appear in the producer's `output_schema` with a compatible primitive type (string/number/integer/boolean/array/object). Deeper checks (recursive `$ref`, `oneOf`/`anyOf`/`allOf`, conditional schemas) are best effort; an orchestrator MAY skip them and MUST NOT reject a file solely because such a check is undecidable.
- If the narrow check fails, the orchestrator MUST stop before any agent runs.
- At runtime, `output_schema` validation continues to apply per `ext:io-schema`. `input_schema` MAY additionally be validated when the consumer starts; on mismatch the consumer MUST be treated as failed.

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
- `prompt_vars` participate in `{{ ... }}` substitution per the merge precedence defined in section 2.6: frontmatter → profile → memory → `prompt_vars` (later wins). On any conflict (frontmatter, profile, or memory), `prompt_vars` win.
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

- `fixtures` is a path/URI to recorded run outputs. Recommended layout: `<fixtures>/<agent_name>.json` for single-shot agents, `<fixtures>/<agent_name>.<iteration>.json` (zero-based) for agents that loop via `ext:control-flow` or `ext:human-in-the-loop`.
- When a fixture is present for an agent (and matches the iteration index, if applicable), the orchestrator MUST use it instead of invoking the model and MUST NOT incur cost for that agent.
- When a fixture is missing, the orchestrator MUST fail the agent (no silent fallback to live calls in `dry_run`).
- Replay support for `ext:streaming` is optional in v0.3; an orchestrator that does not support streaming replay MUST fail fast on a `streaming: true` producer rather than synthesize chunks.
- `ext:eval` MAY run against replayed outputs.

### 3.29 Compatibility matrix

This subsection is **informative**. It summarizes interactions between extensions that are stated normatively in the individual rules above. If the matrix and the prose disagree, the prose wins.

Legend:

- **requires** — A cannot function without B; an orchestrator advertising A MUST also advertise B.
- **extends** — A adds fields/semantics on top of B; supporting A is meaningful only when B is also supported.
- **supersedes** — A replaces a part of B's surface when both are supported.
- **relaxes** — A loosens a Core rule for a scoped pair of constructs.
- **interacts** — A and B have defined cross-rules but neither requires the other.
- **soft-requires** — A degrades gracefully without B (specific behavior documented), but is most useful with B.

| Extension               | Relation       | Other                                                          | Rule lives in |
| ----------------------- | -------------- | -------------------------------------------------------------- | ------------- |
| `ext:streaming`         | relaxes        | Core 2.3 (wave barrier)                                        | 3.20          |
| `ext:streaming`         | interacts      | `ext:io-schema`                                                | 3.20          |
| `ext:streaming`         | interacts      | `ext:checkpoints`                                              | 3.21          |
| `ext:streaming`         | interacts      | `ext:dry-run-replay`                                           | 3.28          |
| `ext:checkpoints`       | interacts      | `ext:hosts` (host-pinned resume)                               | 3.21          |
| `ext:budget`            | supersedes     | `ext:constraints` (`max_cost`)                                 | 3.19          |
| `ext:budget`            | soft-requires  | `ext:cost-routing` (for `degrade_model`)                       | 3.19          |
| `ext:cost-routing`      | extends        | `ext:models`                                                   | 3.24          |
| `ext:plugins`           | extends        | `ext:tools`                                                    | 3.16          |
| `ext:profiles`          | interacts      | Core 2.1 (resolved before validation)                          | 3.17          |
| `ext:profiles`          | interacts      | 2.6 substitution merge order                                   | 2.6 / 3.17    |
| `ext:contracts`         | extends        | `ext:io-schema`                                                | 3.26          |
| `ext:human-in-the-loop` | requires       | `ext:control-flow` (reuses `loop:`)                            | 3.23          |
| `ext:human-in-the-loop` | soft-requires  | `ext:reliability` (for `timeout`)                              | 3.23          |
| `ext:eval`              | interacts      | `ext:reliability` (`## Quality Checks`)                        | 3.18          |
| `ext:eval`              | interacts      | `ext:dry-run-replay`                                           | 3.28          |
| `ext:dry-run-replay`    | extends        | `ext:run-modes`                                                | 3.28          |
| `ext:dry-run-replay`    | interacts      | `ext:control-flow` (per-iteration fixtures)                    | 3.28          |
| `ext:dry-run-replay`    | interacts      | `ext:human-in-the-loop` (loop iterations)                      | 3.28          |
| `ext:memory`            | extends        | Core 2.4 / 2.6 (adds `memory.` namespace)                      | 2.6 / 3.8     |
| `ext:prompt-templates`  | interacts      | 2.6 substitution merge order                                   | 2.6 / 3.27    |
| `ext:subagents`         | interacts      | Core 2.3 (ad-hoc invocation alongside waves)                   | 3.14          |
| `ext:hosts`             | interacts      | `ext:secrets` (host credentials)                               | 3.12          |
| `ext:hosts`             | interacts      | `ext:constraints` (`allowed_paths`/`allowed_domains` per host) | 3.12          |
| `ext:i18n`              | extends        | Core 2.4 (substitution within selected language block)         | 3.25          |
| All extensions          | constrained by | Section 4.1 (no runtime gating of agent set/edges)             | 4.1           |

---

## 4. What this format is NOT

- Not a programming language. No conditionals beyond `loop.if`, no expressions, no functions.
- Not a replacement for orchestrator code. The orchestrator still implements the execution engine.
- Not a single-agent prompt file. Use AGENTS.md for that.
- Not tied to any model provider, framework, or runtime.

### 4.1 Conditional logic boundary (normative)

Conditional logic in a PROJECT.md file is permitted **only** in three places:

1. `loop.if` (`ext:control-flow`) — controlling re-execution of an existing agent.
2. `## On Failure` (`ext:reliability`) — reacting to an agent's failure.
3. `human_review` (`ext:human-in-the-loop`) — reusing the `loop:` form, which is still case (1).

This boundary is about the **composition** of the project — the set of agents and the existence of edges between them — not about how many times a loop iterates or whether streaming/HITL causes timing overlap. Loops, retries, streaming, and human-review pauses do **not** violate the boundary.

Any other runtime-data-driven decision that would change **which** agents exist, **whether** an agent runs at all, or the **edges** of the wave graph is out of scope for this spec. Specifically:

- A PROJECT.md MUST NOT introduce fields that gate an agent's execution on runtime data — including but not limited to `skip_if`, `run_if`, `enabled_if`, `unless`, `cond`, `gate`, `predicate`, `only_when`, `branch_on`, dynamic `wave` selection, or runtime-computed `after`.
- The set of agents and the wave graph MUST be statically determinable from the file alone, before any agent runs.
- Logic that depends on agent output ("if the article is in English, skip translation"; "if no results, try a different source") MUST live **inside an agent's prompt**, not in the file structure. The agent decides and produces output; downstream agents adapt via their prompts.

Rationale: the wave graph is the auditable contract of the project. Once runtime data can reshape it, PROJECT.md becomes a programming language and loses its review, plan, and replay properties.

Enforcement: per section 2.5(7), orchestrators MUST reject (not ignore) unknown agent inline fields whose names match the gating prefix pattern. This is a deliberate, class-level exception to forward compatibility — it closes the entire family of names rather than enumerating three.

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
