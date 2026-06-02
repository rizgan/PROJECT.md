# PROJECT.md reference validator

![PROJECT.md](../project.md.png)

A small Python validator for PROJECT.md `v0.2` Core conformance.

It is **not** an orchestrator — it only parses and validates files. Useful for CI and for catching mistakes before a real run.

## Install

```bash
pip install pyyaml
```

## Use

```bash
python validate.py ../examples/minimal.md
python validate.py ../examples/news-pipeline.md
python validate.py ../examples/*.md
```

Exit code `0` if all files are valid, `1` otherwise.

## What it checks

- Filename matches `PROJECT.md`, `PROJECT-<id>.md`, or `PROJECT_<id>.md`.
- YAML frontmatter is present and well-formed.
- Required fields `spec_version`, `id`, `name` are set.
- `spec_version` is supported.
- `## Agents` section exists and has at least one agent.
- Each agent has a valid name and `wave: <int ≥ 1>`.
- `after:` references existing agents in earlier waves.
- `{{ variable }}` references resolve to frontmatter fields, secrets, or memory keys.

Unknown sections and unknown fields are accepted (forward compatibility).

## Limits

- Extensions (`ext:io-schema`, `ext:constraints`, etc.) are recognised structurally but not deeply validated.
- This validator does not execute anything.
