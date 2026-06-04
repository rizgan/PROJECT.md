---
spec_version: 0.5
id: PROJECT_test
name: test pipeline
topic: release notes
---

# PROJECT_test

<!-- markdownlint-disable MD022 -->

## Agents

### writer
wave: 1

Write a concise summary about: {{ topic }}.

### reviewer
wave: 2
after: writer

Check the summary for clarity and factual consistency.
Return approved or rejected with one short reason.
