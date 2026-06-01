# PROJECT.md — a config file for multi-agent pipelines

We have [AGENTS.md](https://agents.md) for telling **one agent** how to behave in a repo. We don't have a standard for telling an **orchestrator** how to run an entire multi-agent project.

That's the gap PROJECT.md fills.

One Markdown file describes the whole pipeline. An orchestrator reads it and runs it. No glue code.

## What it looks like

```markdown
---
spec_version: 0.1
id: PROJECT-01
name: Tech News Daily
schedule: "0 8 * * *"
language: [en, ru, ar]
max_cost: 1.00 USD
---

## Agents

### collector
wave: 1
provider: anthropic
model: claude-haiku-4-5
tools: [web_search]
Collect 5 top stories from the sources below.

### translator
wave: 2
after: collector
provider: anthropic
model: claude-sonnet-4-6
Translate each story into: {{ language }}.

### image_finder
wave: 2
after: collector
provider: openai
model: gpt-4o
Find a free-to-use image for each story.

### publisher
wave: 3
after: [translator, image_finder]
tools: [wordpress_api, telegram_bot]
Publish the result.
```

That's the whole pipeline. `wave` says when. `after` says from whom. Same-wave agents run in parallel. Different agents use different models and providers. The execution graph is data, not code.

## Why this matters

**Pipelines become readable.** A non-engineer can see what the system does. Reviews on GitHub stop being "what did this Python change do?" and start being "should the translator be cheaper?"

**Models become a config decision.** Use `claude-haiku` for cheap steps, `gpt-4o` where it earns its keep — declared per agent, changed in seconds.

**Safety is built in.** A `## Constraints` section declares what agents may and may not do. `max_cost` in frontmatter caps the entire run. The orchestrator enforces both before any action executes — the difference between a controlled system and an expensive surprise.

**Same orchestrator runs all your projects.** A new pipeline is a new file, not a new codebase.

## How it compares

- **AGENTS.md** — instructions for one agent in a repo. PROJECT.md is one layer up: the pipeline of agents.
- **CrewAI / LangGraph / AutoGen** — powerful, but you write Python. PROJECT.md is declarative and framework-independent.
- **Google ADK** — code-first with strong typing. PROJECT.md trades expressive power for readability and portability.

They're complementary, not competing.

## v0.1 today

The spec is split into a tiny **Core** (frontmatter + agents + waves) that any orchestrator must support, and **Extensions** (tools, secrets, models, constraints, memory, hooks, loops, schemas) that orchestrators can opt into. Core stays small on purpose — if a feature isn't needed by 80% of pipelines, it's an extension.

Repo, spec, examples, and a reference validator:
**https://github.com/rizgan/PROJECT.md**

If you're building multi-agent systems and the format is missing something you actually need — open an issue. That's the most useful kind of feedback before `v1.0`.
