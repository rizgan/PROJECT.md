"""
Reference validator for PROJECT.md v0.1.

Validates Core conformance (section 2 of SPEC.md). Extensions are recognised
but not deeply validated; unknown fields and sections are accepted per the
forward-compatibility rule.

Usage:
    python validate.py path/to/PROJECT.md [more.md ...]

Exit code 0 if all files are valid, 1 otherwise.

Dependencies: PyYAML.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

SUPPORTED_SPEC_VERSIONS = {"0.1"}

FILENAME_RE = re.compile(r"^PROJECT(-[A-Za-z0-9_-]+)?\.md$")
ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
AGENT_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
VAR_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*\}\}")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


@dataclass
class Agent:
    name: str
    wave: int
    after: list[str] = field(default_factory=list)
    extra_fields: dict[str, Any] = field(default_factory=dict)
    body: str = ""


@dataclass
class Project:
    spec_version: str
    id: str
    name: str
    frontmatter: dict[str, Any]
    agents: list[Agent]
    sections: dict[str, str]


class ValidationError(Exception):
    pass


def parse(path: Path) -> Project:
    if not FILENAME_RE.match(path.name):
        raise ValidationError(
            f"{path.name}: filename must match PROJECT.md or PROJECT-<id>.md"
        )

    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        raise ValidationError(f"{path.name}: missing YAML frontmatter block")

    fm_raw, body = m.group(1), m.group(2)
    try:
        fm = yaml.safe_load(fm_raw) or {}
    except yaml.YAMLError as e:
        raise ValidationError(f"{path.name}: invalid YAML frontmatter: {e}")
    if not isinstance(fm, dict):
        raise ValidationError(f"{path.name}: frontmatter must be a mapping")

    for required in ("spec_version", "id", "name"):
        if required not in fm:
            raise ValidationError(f"{path.name}: missing required field '{required}'")

    spec_version = str(fm["spec_version"])
    if spec_version not in SUPPORTED_SPEC_VERSIONS:
        raise ValidationError(
            f"{path.name}: unsupported spec_version '{spec_version}' "
            f"(supported: {sorted(SUPPORTED_SPEC_VERSIONS)})"
        )

    if not ID_RE.match(str(fm["id"])):
        raise ValidationError(f"{path.name}: id must match [A-Za-z0-9_-]+")

    sections = _split_sections(body)
    if "agents" not in sections:
        raise ValidationError(f"{path.name}: missing required section '## Agents'")

    agents = _parse_agents(sections["agents"], path.name)
    if not agents:
        raise ValidationError(f"{path.name}: ## Agents section has no agents")

    _validate_waves_and_refs(agents, path.name)
    _validate_variables(agents, fm, sections, path.name)

    return Project(
        spec_version=spec_version,
        id=str(fm["id"]),
        name=str(fm["name"]),
        frontmatter=fm,
        agents=agents,
        sections=sections,
    )


def _split_sections(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current_name: str | None = None
    buf: list[str] = []
    for line in body.splitlines():
        h = re.match(r"^##\s+(.+?)\s*$", line)
        if h and not line.startswith("###"):
            if current_name is not None:
                sections[current_name] = "\n".join(buf).strip()
            current_name = h.group(1).strip().lower()
            buf = []
        else:
            buf.append(line)
    if current_name is not None:
        sections[current_name] = "\n".join(buf).strip()
    return sections


def _parse_agents(section_body: str, fname: str) -> list[Agent]:
    chunks = re.split(r"^###\s+", section_body, flags=re.MULTILINE)
    agents: list[Agent] = []
    for chunk in chunks[1:]:
        lines = chunk.splitlines()
        name = lines[0].strip()
        if not AGENT_NAME_RE.match(name):
            raise ValidationError(
                f"{fname}: agent name '{name}' must match [a-z][a-z0-9_]*"
            )

        inline: dict[str, Any] = {}
        body_start = len(lines)
        for i, line in enumerate(lines[1:], start=1):
            if not line.strip():
                body_start = i
                break
            kv = re.match(r"^([a-z_][a-z0-9_]*)\s*:\s*(.+?)\s*$", line)
            if not kv:
                body_start = i
                break
            try:
                inline[kv.group(1)] = yaml.safe_load(kv.group(2))
            except yaml.YAMLError:
                inline[kv.group(1)] = kv.group(2)
        body = "\n".join(lines[body_start:]).strip()

        if "wave" not in inline:
            raise ValidationError(f"{fname}: agent '{name}' missing required 'wave'")
        wave = inline["wave"]
        if not isinstance(wave, int) or wave < 1:
            raise ValidationError(
                f"{fname}: agent '{name}' wave must be integer >= 1, got {wave!r}"
            )

        after_raw = inline.get("after", [])
        if after_raw is None:
            after = []
        elif isinstance(after_raw, str):
            after = [after_raw]
        elif isinstance(after_raw, list):
            after = [str(x) for x in after_raw]
        else:
            raise ValidationError(
                f"{fname}: agent '{name}' 'after' must be string or list"
            )

        extra = {k: v for k, v in inline.items() if k not in {"wave", "after"}}
        agents.append(Agent(name=name, wave=wave, after=after, extra_fields=extra, body=body))
    return agents


def _validate_waves_and_refs(agents: list[Agent], fname: str) -> None:
    names = {a.name for a in agents}
    if len(names) != len(agents):
        raise ValidationError(f"{fname}: duplicate agent names")
    by_name = {a.name: a for a in agents}
    for a in agents:
        for dep in a.after:
            if dep not in names:
                raise ValidationError(
                    f"{fname}: agent '{a.name}' references unknown agent '{dep}' in after"
                )
            if by_name[dep].wave >= a.wave:
                raise ValidationError(
                    f"{fname}: agent '{a.name}' (wave {a.wave}) cannot depend on "
                    f"'{dep}' (wave {by_name[dep].wave}); dependency must be in an earlier wave"
                )


def _validate_variables(
    agents: list[Agent], fm: dict, sections: dict, fname: str
) -> None:
    available: set[str] = set(fm.keys())
    if "secrets" in sections:
        for line in sections["secrets"].splitlines():
            kv = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:", line)
            if kv:
                available.add(kv.group(1))
    if "memory" in sections:
        for line in sections["memory"].splitlines():
            kv = re.match(r"^-\s*([A-Za-z_][A-Za-z0-9_]*)\s*:", line)
            if kv:
                available.add(f"memory.{kv.group(1)}")

    for a in agents:
        for ref in VAR_RE.findall(a.body):
            root = ref.split(".")[0]
            if ref in available or root in available:
                continue
            if ref.startswith("memory."):
                raise ValidationError(
                    f"{fname}: agent '{a.name}' references unknown memory key '{ref}'"
                )
            raise ValidationError(
                f"{fname}: agent '{a.name}' references unknown variable '{ref}'"
            )


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    failed = 0
    for arg in argv:
        path = Path(arg)
        try:
            project = parse(path)
            waves = sorted({a.wave for a in project.agents})
            print(f"OK  {path}  id={project.id}  agents={len(project.agents)}  waves={waves}")
        except ValidationError as e:
            failed += 1
            print(f"FAIL {e}")
        except Exception as e:
            failed += 1
            print(f"FAIL {path}: {type(e).__name__}: {e}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
