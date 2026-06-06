from __future__ import annotations

import argparse
import json
import operator
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any

import yaml
from dotenv import load_dotenv
from jsonschema import validate as jsonschema_validate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict


SUPPORTED_EXTENSIONS = {"ext:models", "ext:tools", "ext:io-schema"}
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
AGENT_HEADING_RE = re.compile(r"^###\s+([a-z][a-z0-9_]*)\s*$", re.IGNORECASE)
INLINE_FIELD_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$")
TEMPLATE_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}")


def merge_dicts(left: dict[str, str], right: dict[str, str]) -> dict[str, str]:
	merged = dict(left or {})
	merged.update(right or {})
	return merged


class PipelineState(TypedDict):
	outputs: Annotated[dict[str, str], merge_dicts]
	trace: Annotated[list[str], operator.add]


@dataclass
class AgentSpec:
	name: str
	wave: int
	after: list[str]
	prompt: str
	provider: str | None
	model: str | None
	tools: list[str]
	output_schema: str | None


@dataclass
class ProjectSpec:
	frontmatter: dict[str, Any]
	extensions: set[str]
	tools_catalog: set[str]
	agents: list[AgentSpec]
	root_dir: Path


class Executor:
	def invoke(self, agent: AgentSpec, prompt: str, upstream: dict[str, str]) -> str:
		raise NotImplementedError


class MockExecutor(Executor):
	def invoke(self, agent: AgentSpec, prompt: str, upstream: dict[str, str]) -> str:
		if agent.name == "publisher":
			summary = "\n".join(f"- {name}: {text[:120]}" for name, text in upstream.items())
			return f"Pipeline complete for {agent.name}.\n\nUpstream summary:\n{summary}"

		context = ""
		if upstream:
			context = "\n\nUpstream context:\n" + "\n".join(
				f"- {name}: {text[:180]}" for name, text in upstream.items()
			)
		tool_hint = f"\nTools used: {', '.join(agent.tools)}" if agent.tools else ""
		return f"{prompt}{context}{tool_hint}"


class LLMExecutor(Executor):
	def __init__(self, base_url: str, api_key: str):
		self.base_url = base_url
		self.api_key = api_key
		self.clients: dict[str, ChatOpenAI] = {}

	def _client_for(self, model_name: str) -> ChatOpenAI:
		key = model_name.strip()
		if key not in self.clients:
			self.clients[key] = ChatOpenAI(
				model=key,
				api_key=self.api_key,
				base_url=self.base_url,
				temperature=0.2,
				timeout=60,
				max_retries=1,
			)
		return self.clients[key]

	def invoke(self, agent: AgentSpec, prompt: str, upstream: dict[str, str]) -> str:
		if not agent.model:
			raise ValueError(
				f"Agent '{agent.name}' is missing 'model' while running in LLM mode."
			)

		system_text = (
			"You are one agent in a PROJECT.md pipeline. "
			"Return clear, compact output."
		)
		user_text = prompt
		if upstream:
			upstream_blob = "\n\n".join(
				f"[{name}]\n{truncate_text(text, limit=700)}"
				for name, text in sorted(upstream.items())
			)
			user_text += f"\n\nInputs from dependencies:\n{upstream_blob}"
		if agent.tools:
			user_text += f"\n\nAllowed tools (informational): {', '.join(agent.tools)}"

		response = self._client_for(agent.model).invoke(
			[
				("system", system_text),
				("user", user_text),
			]
		)
		return str(response.content).strip()


def truncate_text(text: str, limit: int) -> str:
	if len(text) <= limit:
		return text
	return text[: limit - 20] + "\n...[truncated]..."


def parse_project_file(path: Path) -> ProjectSpec:
	text = path.read_text(encoding="utf-8")
	frontmatter = parse_frontmatter(text)
	extensions = set(frontmatter.get("extensions", []))
	tools_catalog = parse_tools_catalog(text)
	agents = parse_agents(text)

	validate_core(frontmatter, agents)
	validate_extensions(extensions)
	resolve_default_dependencies(agents)
	validate_after_dependencies(agents)
	validate_template_variables(frontmatter, agents)
	validate_extension_fields(extensions, tools_catalog, agents)

	return ProjectSpec(
		frontmatter=frontmatter,
		extensions=extensions,
		tools_catalog=tools_catalog,
		agents=agents,
		root_dir=path.parent,
	)


def parse_frontmatter(text: str) -> dict[str, Any]:
	match = FRONTMATTER_RE.search(text)
	if not match:
		raise ValueError("Missing required YAML frontmatter.")
	data = yaml.safe_load(match.group(1))
	if not isinstance(data, dict):
		raise ValueError("Frontmatter must be a YAML mapping.")
	return data


def extract_section_lines(text: str, section_name: str) -> list[str]:
	lines = text.splitlines()
	start = None
	end = len(lines)
	target = f"## {section_name}".lower()

	for idx, line in enumerate(lines):
		if line.strip().lower() == target:
			start = idx + 1
			break

	if start is None:
		return []

	for idx in range(start, len(lines)):
		if lines[idx].startswith("## "):
			end = idx
			break

	return lines[start:end]


def parse_tools_catalog(text: str) -> set[str]:
	section = extract_section_lines(text, "Tools")
	tools: set[str] = set()
	for line in section:
		stripped = line.strip()
		if stripped.startswith("- "):
			tool_name = stripped[2:].strip()
			if tool_name:
				tools.add(tool_name)
	return tools


def parse_agents(text: str) -> list[AgentSpec]:
	lines = extract_section_lines(text, "Agents")
	if not lines:
		raise ValueError("Missing required section: ## Agents")

	agents: list[AgentSpec] = []
	i = 0
	while i < len(lines):
		heading_match = AGENT_HEADING_RE.match(lines[i].strip())
		if not heading_match:
			i += 1
			continue

		name = heading_match.group(1)
		i += 1

		inline: dict[str, Any] = {}
		while i < len(lines):
			line = lines[i]
			if not line.strip():
				i += 1
				break
			if lines[i].strip().startswith("### "):
				break

			field_match = INLINE_FIELD_RE.match(line.strip())
			if not field_match:
				break

			key = field_match.group(1)
			raw_value = field_match.group(2)
			inline[key] = yaml.safe_load(raw_value) if raw_value else ""
			i += 1

		prompt_lines: list[str] = []
		while i < len(lines):
			if lines[i].strip().startswith("### "):
				break
			prompt_lines.append(lines[i])
			i += 1

		wave = inline.get("wave")
		if not isinstance(wave, int) or wave < 1:
			raise ValueError(f"Agent '{name}' must define 'wave' as integer >= 1.")

		after_raw = inline.get("after")
		if after_raw is None:
			after = []
		elif isinstance(after_raw, str):
			after = [after_raw]
		elif isinstance(after_raw, list) and all(isinstance(x, str) for x in after_raw):
			after = after_raw
		else:
			raise ValueError(f"Agent '{name}' has invalid 'after' value.")

		tools_raw = inline.get("tools")
		if tools_raw is None:
			tools = []
		elif isinstance(tools_raw, str):
			tools = [tools_raw]
		elif isinstance(tools_raw, list) and all(isinstance(x, str) for x in tools_raw):
			tools = tools_raw
		else:
			raise ValueError(f"Agent '{name}' has invalid 'tools' value.")

		prompt = "\n".join(prompt_lines).strip()
		agents.append(
			AgentSpec(
				name=name,
				wave=wave,
				after=after,
				prompt=prompt,
				provider=inline.get("provider"),
				model=inline.get("model"),
				tools=tools,
				output_schema=inline.get("output_schema"),
			)
		)

	if not agents:
		raise ValueError("Section ## Agents must contain at least one agent.")
	return agents


def validate_core(frontmatter: dict[str, Any], agents: list[AgentSpec]) -> None:
	for required in ("spec_version", "id", "name"):
		if required not in frontmatter:
			raise ValueError(f"Missing required frontmatter field: {required}")

	spec_version = str(frontmatter["spec_version"])
	if not (spec_version == "0.5" or spec_version.startswith("0.5.")):
		raise ValueError(
			f"Unsupported spec_version '{spec_version}'. Expected 0.5 or 0.5.x."
		)

	names = [a.name for a in agents]
	if len(names) != len(set(names)):
		raise ValueError("Agent names must be unique.")


def validate_extensions(extensions: set[str]) -> None:
	unknown = sorted(extensions - SUPPORTED_EXTENSIONS)
	if unknown:
		items = ", ".join(unknown)
		raise ValueError(f"Unsupported declared extensions in demo runner: {items}")


def resolve_default_dependencies(agents: list[AgentSpec]) -> None:
	by_wave: dict[int, list[str]] = {}
	for agent in agents:
		by_wave.setdefault(agent.wave, []).append(agent.name)

	for agent in agents:
		if agent.after:
			continue
		agent.after = by_wave.get(agent.wave - 1, [])


def validate_after_dependencies(agents: list[AgentSpec]) -> None:
	by_name = {a.name: a for a in agents}
	for agent in agents:
		for dep in agent.after:
			if dep not in by_name:
				raise ValueError(f"Agent '{agent.name}' depends on unknown agent '{dep}'.")
			if by_name[dep].wave >= agent.wave:
				raise ValueError(
					f"Agent '{agent.name}' depends on '{dep}' from same/later wave."
				)


def validate_template_variables(frontmatter: dict[str, Any], agents: list[AgentSpec]) -> None:
	unresolved: set[str] = set()
	for agent in agents:
		for var in TEMPLATE_RE.findall(agent.prompt):
			if resolve_dot_path(frontmatter, var) is None:
				unresolved.add(var)
	if unresolved:
		items = ", ".join(sorted(unresolved))
		raise ValueError(f"Unresolved template variables: {items}")


def validate_extension_fields(
	extensions: set[str], tools_catalog: set[str], agents: list[AgentSpec]
) -> None:
	for agent in agents:
		if agent.model or agent.provider:
			if "ext:models" not in extensions:
				raise ValueError(
					f"Agent '{agent.name}' uses provider/model but ext:models is not declared."
				)

		if agent.tools:
			if "ext:tools" not in extensions:
				raise ValueError(
					f"Agent '{agent.name}' uses tools but ext:tools is not declared."
				)
			missing = sorted(set(agent.tools) - tools_catalog)
			if missing:
				raise ValueError(
					f"Agent '{agent.name}' references unknown tools: {', '.join(missing)}"
				)

		if agent.output_schema:
			if "ext:io-schema" not in extensions:
				raise ValueError(
					f"Agent '{agent.name}' uses output_schema but ext:io-schema is not declared."
				)


def resolve_dot_path(data: dict[str, Any], path: str) -> Any:
	cur: Any = data
	for part in path.split("."):
		if not isinstance(cur, dict) or part not in cur:
			return None
		cur = cur[part]
	return cur


def render_prompt(prompt: str, frontmatter: dict[str, Any]) -> str:
	def repl(match: re.Match[str]) -> str:
		key = match.group(1)
		value = resolve_dot_path(frontmatter, key)
		if value is None:
			raise ValueError(f"Unresolved variable '{key}'.")
		return str(value)

	return TEMPLATE_RE.sub(repl, prompt)


def parse_model_output(raw: str) -> Any:
	text = raw.strip()
	if not text:
		return ""
	if text.startswith("{") or text.startswith("["):
		try:
			return json.loads(text)
		except json.JSONDecodeError:
			return raw
	return raw


def apply_output_schema_validation(spec: ProjectSpec, agent: AgentSpec, output: str) -> None:
	if not agent.output_schema:
		return

	schema_path = (spec.root_dir / agent.output_schema).resolve()
	if not schema_path.exists():
		raise ValueError(
			f"Agent '{agent.name}' output_schema does not exist: {schema_path}"
		)

	schema = json.loads(schema_path.read_text(encoding="utf-8"))
	candidate = parse_model_output(output)
	jsonschema_validate(instance=candidate, schema=schema)


def resolve_executor(run_mode: str, env_file: Path) -> Executor:
	load_dotenv(env_file, override=False)
	base_url = (os.getenv("url_base") or os.getenv("OPENAI_BASE_URL") or "").strip()
	api_key = (os.getenv("api_key") or os.getenv("OPENAI_API_KEY") or "").strip()

	if run_mode == "mock":
		return MockExecutor()

	if not base_url or not api_key:
		raise ValueError(
			"LLM mode requires url_base/api_key (or OPENAI_BASE_URL/OPENAI_API_KEY) in .env"
		)
	return LLMExecutor(base_url=base_url, api_key=api_key)


def build_graph(spec: ProjectSpec, executor: Executor):
	graph = StateGraph(PipelineState)
	by_name = {agent.name: agent for agent in spec.agents}
	outgoing: dict[str, set[str]] = {name: set() for name in by_name}

	for agent in spec.agents:
		prompt_text = render_prompt(agent.prompt, spec.frontmatter)

		def make_node(current: AgentSpec, rendered_prompt: str):
			def node(state: PipelineState) -> PipelineState:
				print(f"[start] {current.name} (wave {current.wave})", flush=True)
				upstream = {
					dep: state.get("outputs", {}).get(dep, "")
					for dep in current.after
				}
				output = executor.invoke(current, rendered_prompt, upstream)
				apply_output_schema_validation(spec, current, output)
				print(f"[done]  {current.name}", flush=True)
				return {
					"outputs": {current.name: output},
					"trace": [f"{current.name} (wave {current.wave})"],
				}

			return node

		graph.add_node(agent.name, make_node(agent, prompt_text))

	for agent in spec.agents:
		if not agent.after:
			graph.add_edge(START, agent.name)
			continue
		for dep in agent.after:
			graph.add_edge(dep, agent.name)
			outgoing[dep].add(agent.name)

	leaves = [name for name, deps in outgoing.items() if not deps]
	for leaf in leaves:
		graph.add_edge(leaf, END)

	return graph.compile()


def print_wave_layout(agents: list[AgentSpec]) -> None:
	by_wave: dict[int, list[str]] = {}
	for agent in agents:
		by_wave.setdefault(agent.wave, []).append(agent.name)

	print("=== Wave Layout ===")
	for wave in sorted(by_wave):
		names = ", ".join(sorted(by_wave[wave]))
		print(f"wave {wave}: {names}")


def run(project_file: Path, run_mode: str, env_file: Path) -> None:
	spec = parse_project_file(project_file)
	executor = resolve_executor(run_mode=run_mode, env_file=env_file)

	print_wave_layout(spec.agents)
	app = build_graph(spec, executor)
	result = app.invoke({"outputs": {}, "trace": []})

	print("\n=== Execution Trace ===")
	for item in result.get("trace", []):
		print(f"- {item}")

	print("\n=== Agent Outputs ===")
	for agent in sorted(spec.agents, key=lambda x: (x.wave, x.name)):
		print(f"\n[{agent.name}]")
		print(result.get("outputs", {}).get(agent.name, ""))


def main() -> None:
	parser = argparse.ArgumentParser(description="Run PROJECT.md file via LangGraph")
	parser.add_argument(
		"project_file",
		nargs="?",
		default="PROJECT-langgraph-support.md",
		help="Path to a PROJECT.md file (default: PROJECT-langgraph-support.md)",
	)
	parser.add_argument(
		"--mode",
		choices=["mock", "llm"],
		default="mock",
		help="Execution mode: mock (default) or llm",
	)
	parser.add_argument(
		"--env-file",
		default=str(Path(__file__).resolve().parent.parent / ".env"),
		help="Path to .env with provider credentials",
	)
	args = parser.parse_args()

	run(
		project_file=Path(args.project_file),
		run_mode=args.mode,
		env_file=Path(args.env_file),
	)


if __name__ == "__main__":
	main()
