# PROJECT.md

![PROJECT.md](project.md.png)

**Language / Язык / 语言 / 言語 / 언어:**
[English](README.md) · [中文](README.zh.md) · [हिंदी](README.hi.md) · [Русский](README.ru.md) · [Português](README.pt.md) · [Español](README.es.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

---

An open file format for **multi-agent pipelines**.

One Markdown file describes the whole project: which agents run, in what order, with which models, what they're allowed to do, and what happens when they fail. An orchestrator reads the file and executes the pipeline — no glue code required.

If [AGENTS.md](https://agents.md) tells **one agent** how to behave in a repo, PROJECT.md tells **an orchestrator** how to run an entire project.

---

## Minimal example

```markdown
---
spec_version: 0.5
id: PROJECT-01
name: Hello pipeline
---

## Agents

### writer
wave: 1
Write a one-paragraph summary of: {{ topic }}.

### reviewer
wave: 2
after: writer
Check the summary for factual errors. Return `approved` or `rejected`.
```

That's a valid PROJECT.md. Everything else is optional.

---

## Why

Today, defining a multi-agent pipeline means writing orchestration code. Every new project means new classes, new wiring, new config files. The pipeline definition is data, not code — it belongs in a file.

PROJECT.md is that file.

---

## Design principles

1. **Markdown + YAML frontmatter.** No new language to learn.
2. **Core stays small.** If a feature isn't needed by 80% of pipelines, it goes to Extensions, not Core.
3. **Declarative, not imperative.** The file describes *what*; the orchestrator decides *how*.
4. **Framework-independent.** Any orchestrator can implement it.

---

## How it compares

| Capability                          | AGENTS.md | SKILL.md  | CrewAI yaml   | LangGraph     | Google ADK    | PROJECT.md    |
| ----------------------------------- | :-------: | :-------: | :-----------: | :-----------: | :-----------: | :-----------: |
| Format                              | Markdown  | Markdown  | 2× YAML       | Python code   | Python code   | Markdown+YAML |
| Author profile                      | anyone    | anyone    | developer     | developer     | developer     | anyone        |
| Scope                               | 1 agent   | 1 skill   | pipeline      | pipeline      | pipeline      | pipeline      |
| Single file                         | ✅        | ✅        | ❌ (2 files)  | ❌ (code)     | ❌ (code)     | ✅            |
| Multi-agent pipeline                | ❌        | ❌        | ✅            | ✅            | ✅            | ✅            |
| Sequential execution                | —         | —         | ✅            | ✅            | ✅            | ✅            |
| Parallel execution                  | —         | —         | ✅            | ✅            | ✅            | ✅ (`wave`)   |
| Explicit data dependencies          | —         | —         | implicit      | ✅ (edges)    | implicit      | ✅ (`after`)  |
| Loops / retry on judge              | —         | —         | partial       | ✅            | ✅            | ✅ (ext)      |
| Hierarchical agents                 | —         | —         | ✅            | ✅            | ✅            | ✅ (ext)      |
| Per-agent model & provider          | —         | —         | ✅            | ✅            | ✅            | ✅ (ext)      |
| Tools declaration                   | partial   | partial   | ✅            | ✅            | ✅            | ✅ (ext)      |
| Typed I/O (schema)                  | —         | —         | partial       | ✅            | ✅ (Pydantic) | ✅ (ext)      |
| Secrets as references               | —         | —         | code-level    | code-level    | code-level    | ✅ (ext)      |
| Cross-run memory                    | —         | —         | code-level    | ✅            | code-level    | ✅ (ext)      |
| Lifecycle hooks                     | —         | —         | code-level    | code-level    | code-level    | ✅ (ext)      |
| Cost / budget guardrails            | —         | —         | ❌            | ❌            | ❌            | ✅ (ext)      |
| Action constraints (allow/deny)     | —         | —         | ❌            | ❌            | ❌            | ✅ (ext)      |
| Scheduling (cron)                   | —         | —         | ❌            | ❌            | ❌            | ✅ (ext)      |
| Run modes (dry/test/prod)           | —         | —         | ❌            | ❌            | ❌            | ✅ (ext)      |
| Framework-independent               | ✅        | ✅        | ❌ (CrewAI)   | ❌ (LangGraph)| ❌ (ADK)      | ✅            |
| Human-readable diff in PR review    | ✅        | ✅        | ✅            | ❌            | ❌            | ✅            |

**Read it as:** AGENTS.md and SKILL.md describe *one* unit (an agent, a skill). CrewAI, LangGraph and ADK describe *pipelines* but in code or a framework-specific schema. PROJECT.md is the only format that is both **declarative Markdown** and **framework-independent** for the pipeline layer.

PROJECT.md can optionally reference existing AGENTS.md and SKILL.md files through extensions, while still working perfectly well without them.

> IDE-specific files like `CLAUDE.md`, `GEMINI.md`, `.cursorrules`, `.github/copilot-instructions.md`, `.windsurfrules`, `.clinerules` are intentionally omitted — they share AGENTS.md's scope (single agent, one repo) and only differ in which tool reads them.

---

## Spec

- [SPEC.md](SPEC.md) — full specification (Core + Extensions)
- [examples/PROJECT-minimal.md](examples/PROJECT-minimal.md) — Core-only pipeline
- [examples/PROJECT-etl.md](examples/PROJECT-etl.md) — full ETL/data quality example
- [validator/](validator/) — reference Python validator

## Example: LangGraph support

- [examples/support/langgraph/README.md](examples/support/langgraph/README.md) — setup and run guide
- [examples/support/langgraph/PROJECT-langgraph-10-agents.md](examples/support/langgraph/PROJECT-langgraph-10-agents.md) — 10-agent demo with parallel waves
- Run offline: `python examples/support/langgraph/run_langgraph_project.py examples/support/langgraph/PROJECT-langgraph-10-agents.md --mode mock --env-file examples/support/.env`
- Run with provider: `python examples/support/langgraph/run_langgraph_project.py examples/support/langgraph/PROJECT-langgraph-10-agents.md --mode llm --env-file examples/support/.env`
- Demo stats: 10 agents, 5 waves, 3 parallel waves with 3+3+2 agents, and a successful end-to-end provider run

## Quick check

1. Install dependencies: `pip install -r examples/support/langgraph/requirements.txt`
2. Run the offline demo: `python examples/support/langgraph/run_langgraph_project.py examples/support/langgraph/PROJECT-langgraph-10-agents.md --mode mock --env-file examples/support/.env`
3. Run the provider demo: `python examples/support/langgraph/run_langgraph_project.py examples/support/langgraph/PROJECT-langgraph-10-agents.md --mode llm --env-file examples/support/.env`

---

## Status

`v0.5` — draft. Breaking changes possible until `v1.0`. Pin `spec_version` in your files.

---

## Contributing

Issues and PRs welcome — especially:

- Real use-cases that expose gaps
- Orchestrator implementations
- Pushback on what should *not* be in the spec

## License

Apache-2.0 — see [LICENSE](LICENSE).
