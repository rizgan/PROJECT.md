---
spec_version: 0.5.1
id: PROJECT-langgraph-support
name: LangGraph support demo
topic: retrieval augmented generation
---

## Agents

### writer
wave: 1
Write one concise paragraph about {{ topic }}.

### reviewer
wave: 2
after: writer
Review the writer output. Return `approved` when it is clear and factual.

### publisher
wave: 3
after: [writer, reviewer]
Create a final response that includes writer text and reviewer verdict.
