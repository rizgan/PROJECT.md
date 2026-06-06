# PROJECT.md support example with LangGraph

This folder demonstrates support for PROJECT.md `spec_version: 0.5.1` with LangGraph.

Supported behavior in this demo runner:
- Core: frontmatter, `## Agents`, `wave`, `after`, `{{ variable }}` substitution
- `ext:models`: per-agent `provider` and `model`
- `ext:tools`: `## Tools` catalog + per-agent `tools`
- `ext:io-schema`: per-agent `output_schema` validation via JSON Schema

## Files

- `PROJECT-langgraph-support.md`: compact demo pipeline
- `PROJECT-langgraph-10-agents.md`: full 10-agent example with parallel waves
- `run_langgraph_project.py`: parser + LangGraph executor
- `schemas/*.json`: schemas used by `output_schema`
- `requirements.txt`: Python dependencies

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `.env` in `examples/support` with provider credentials (OpenAI-compatible):

```env
url_base="https://..."
api_key="..."
```

## Run

Mock mode (offline):

```bash
python run_langgraph_project.py PROJECT-langgraph-10-agents.md --mode mock
```

LLM mode:

```bash
python run_langgraph_project.py PROJECT-langgraph-10-agents.md --mode llm --env-file ../.env
```

The output includes:
- wave layout (to see parallel groups)
- execution trace
- output of each of the 10 agents
