---
spec_version: 0.5.1
id: PROJECT-langgraph-10-agents
name: Ten agent LangGraph demo
topic: practical blueprint for AI support chat in SaaS
extensions:
  - ext:models
  - ext:tools
  - ext:io-schema
---

## Tools
- web_search
- summarize
- consistency_check

## Agents

### scout_market
wave: 1
provider: zai
model: glm-4.5-air
tools: [web_search]
output_schema: ./schemas/short_text.json
Find market expectations for {{ topic }} and return concise notes.

### scout_tech
wave: 1
provider: zai
model: glm-4.5-air
tools: [web_search]
output_schema: ./schemas/short_text.json
Find technical constraints for {{ topic }} in production systems.

### scout_risk
wave: 1
provider: zai
model: glm-4.5-air
tools: [web_search]
output_schema: ./schemas/short_text.json
Identify top risks for {{ topic }} and likely mitigation patterns.

### synth_product
wave: 2
after: [scout_market, scout_tech]
provider: zai
model: glm-4.5-air
tools: [summarize]
output_schema: ./schemas/short_text.json
Synthesize a product strategy from upstream inputs.

### synth_ops
wave: 2
after: [scout_tech, scout_risk]
provider: zai
model: glm-4.5-air
tools: [summarize, consistency_check]
output_schema: ./schemas/short_text.json
Synthesize an operations and reliability plan from upstream inputs.

### synth_security
wave: 2
after: [scout_risk]
provider: zai
model: glm-4.5-air
tools: [consistency_check]
output_schema: ./schemas/short_text.json
Create a security baseline and controls shortlist.

### architect
wave: 3
after: [synth_product, synth_ops, synth_security]
provider: zai
model: glm-4.5-air
tools: [summarize]
output_schema: ./schemas/short_text.json
Draft target architecture and rollout phases.

### critic
wave: 3
after: [synth_product, synth_ops, synth_security]
provider: zai
model: glm-4.5-air
tools: [consistency_check]
output_schema: ./schemas/short_text.json
Challenge assumptions, find weak points, suggest fixes.

### editor
wave: 4
after: [architect, critic]
provider: zai
model: glm-4.5-air
tools: [summarize]
output_schema: ./schemas/short_text.json
Merge architecture and critique into a coherent single plan.

### publisher
wave: 5
after: [editor]
provider: zai
model: glm-4.5-air
output_schema: ./schemas/final_text.json
Produce final publishable version with priorities and next 30-day actions.
