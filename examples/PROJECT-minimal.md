---
spec_version: 0.5
id: PROJECT-hello
name: Hello pipeline
topic: how transformer attention works
---

## Agents

### writer
wave: 1
Write a one-paragraph summary of: {{ topic }}.

### reviewer
wave: 2
after: writer
Read the writer's output. Reply with `approved` if it is factually correct
and self-contained, otherwise `rejected` with a one-line reason.
