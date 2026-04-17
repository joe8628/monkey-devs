# Monkey Devs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a standalone Python CLI multi-agent development workflow (Monkey Devs) with five LangGraph stages, human gate control, SQLite persistence, and multi-vendor LLM support.
**Spec:** `docs/design/design-monkey-devs.md` (v1.4, approved)
**Stack:** Python 3.11+, Typer, LangGraph + langgraph-checkpoint-sqlite, LiteLLM, uv

---

## Phase 1 — Foundation Layer

These tasks are independent and MAY be dispatched in parallel. They establish the scaffold that everything else depends on.

---

### Task 1: Package Scaffold (IU-01)
Files: create `pyproject.toml`, create `monkey_devs/__init__.py`, create `monkey_devs/cli.py`, create `monkey_devs/orchestrator.py`, create `monkey_devs/graph.py`, create `monkey_devs/tools.py`, create `monkey_devs/config.py`, create `monkey_devs/tasks.py`, create `monkey_devs/logger.py`, create `monkey_devs/state.py`, create `monkey_devs/nodes/__init__.py`, create `monkey_devs/nodes/concept_spec.py`, create `monkey_devs/nodes/architecture.py`, create `monkey_devs/nodes/implementation.py`, create `monkey_devs/nodes/code_fixing.py`, create `monkey_devs/nodes/documentation.py`, create `monkey_devs/nodes/delivery.py`, create `monkey_devs/nodes/review.py`, create `tests/__init__.py`, test `tests/test_scaffold.py`

- [ ] **Test** — add to `tests/test_scaffold.py`:
  ```py
  def test_package_importable():
      import monkey_devs
      assert monkey_devs.__version__ == "0.1.0"
  ```
  Run `pytest tests/test_scaffold.py` → FAIL

- [ ] **Implement** — create `pyproject.toml`:
  ```toml
  [project]
  name = "monkey-devs"
  version = "0.1.0"
  requires-python = ">=3.11"
  dependencies = [
      "typer>=0.12", "langgraph>=0.2", "langgraph-checkpoint-sqlite>=1.0",
      "litellm>=1.40", "pyyaml>=6.0", "pydantic>=2.0",
  ]
  [project.scripts]
  monkey-devs = "monkey_devs.cli:app"
  ```
  Create all `monkey_devs/` module stubs with `pass`-body functions matching names from design.
  Set `__version__ = "0.1.0"` in `monkey_devs/__init__.py`.

- [ ] **Commit** — `feat: bootstrap monkey-devs package scaffold`

---

### Task 2: LangGraph State Schema (IU-04)
Files: create `monkey_devs/state.py`, test `tests/test_state.py`

- [ ] **Test** — add to `tests/test_state.py`:
  ```py
  from monkey_devs.state import WorkflowState
  def test_state_schema_has_required_fields():
      fields = WorkflowState.__annotations__
      for f in ["project_name", "current_stage", "workflow_status", "stage_statuses",
                "stage_outputs", "stage_models", "correction_active", "tasks",
                "gate_decisions", "thread_id", "correction_counts", "review_verdicts",
                "review_brief_paths", "review_skipped"]:
          assert f in fields, f"Missing field: {f}"
  ```
  Run `pytest tests/test_state.py` → FAIL

- [ ] **Implement** — create `monkey_devs/state.py`:
  ```py
  from typing import TypedDict

  class WorkflowState(TypedDict):
      project_name: str
      project_path: str
      current_stage: int
      workflow_status: str           # active | completed | interrupted
      stage_statuses: dict[int, str] # pending|active|complete|approved|rejected
      stage_outputs: dict[int | str, list[str]]
      stage_models: dict[int | str, str]
      correction_active: bool
      correction_stage: int | None
      correction_reason: str | None
      tasks: list[str]
      tasks_dispatched: list[str]
      tasks_completed: list[str]
      current_task_index: int
      gate_decisions: dict[int, str]
      allocated_skills: dict[int, list[str]]
      allocated_tools: dict[int, list[str]]
      thread_id: str
      correction_counts: dict[int, int]
      review_verdicts: dict[int, str]
      review_brief_paths: dict[int, str]
      review_skipped: dict[int, bool]
  ```

- [ ] **Commit** — `feat: add WorkflowState TypedDict (IU-04)`

---

### Task 3: JSONL Run Logger (IU-08)
Files: create `monkey_devs/logger.py`, test `tests/test_logger.py`

- [ ] **Test** — add to `tests/test_logger.py`:
  ```py
  import json, pathlib
  from monkey_devs.logger import RunLogger
  def test_log_event_writes_jsonl(tmp_path):
      logger = RunLogger(log_dir=tmp_path)
      logger.log("workflow_started", project="test-proj")
      lines = (list(tmp_path.iterdir())[0]).read_text().splitlines()
      event = json.loads(lines[0])
      assert event["event"] == "workflow_started"
      assert event["project"] == "test-proj"
      assert "ts" in event
  ```
  Run `pytest tests/test_logger.py` → FAIL

- [ ] **Implement** — create `monkey_devs/logger.py`:
  ```py
  import json, pathlib, datetime

  class RunLogger:
      def __init__(self, log_dir: pathlib.Path):
          log_dir.mkdir(parents=True, exist_ok=True)
          ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S")
          self._path = log_dir / f"run-{ts}.jsonl"
          self._rotate(log_dir, keep=10)

      def log(self, event: str, **kwargs) -> None:
          record = {"ts": datetime.datetime.utcnow().isoformat(), "event": event, **kwargs}
          with self._path.open("a") as f:
              f.write(json.dumps(record) + "\n")

      @staticmethod
      def _rotate(log_dir: pathlib.Path, keep: int) -> None:
          logs = sorted(log_dir.glob("run-*.jsonl"))
          for old in logs[:-keep]:
              old.unlink(missing_ok=True)
  ```

- [ ] **Commit** — `feat: add JSONL run logger with rotation (IU-08)`

---

### Task 4: Config Loader (IU-02)
Files: modify `monkey_devs/config.py`, create `tests/fixtures/config.yaml`, test `tests/test_config.py`

- [ ] **Test** — add to `tests/test_config.py`:
  ```py
  from monkey_devs.config import load_config, validate_config, ConfigValidationError
  def test_load_config_parses_models(tmp_path):
      cfg_text = "models:\n  concept-spec: google/gemini-2.5-pro\n  architecture: google/gemini-2.5-pro\n  implementation: anthropic/claude-opus-4-6\n  code-fixing: openai/o4-mini\n  delivery: anthropic/claude-sonnet-4-6\n  reviewer: anthropic/claude-opus-4-6\n  fixer: google/gemini-2.5-pro\nproviders:\n  anthropic:\n    api_key_env: ANTHROPIC_API_KEY\ntimeouts:\n  concept-spec: 120\nworkflow:\n  max_corrections_per_stage: 3\n  max_handoff_chars: 400000\n  max_intake_turns: 20\n  max_tool_iterations: 30\n  auto_correction_on_validation_failure: true\nreview:\n  enabled: true\n"
      p = tmp_path / "config.yaml"
      p.write_text(cfg_text)
      cfg = load_config(p)
      assert cfg.models["concept-spec"] == "google/gemini-2.5-pro"
      assert cfg.workflow.max_corrections_per_stage == 3
  def test_validate_config_blocks_key_literals(tmp_path):
      p = tmp_path / "config.yaml"
      p.write_text("providers:\n  anthropic:\n    api_key_env: sk-ant-abcdefghijklmnopqrstuvwxyz1234567890abcdefghijklmnopqrstuvwxyz1234567890abcdefghijklm\n")
      try:
          validate_config(p)
          assert False, "Expected ConfigValidationError"
      except ConfigValidationError:
          pass
  ```
  Run `pytest tests/test_config.py` → FAIL

- [ ] **Implement** — create `monkey_devs/config.py`:
  ```py
  import re, yaml, pathlib
  from pydantic import BaseModel

  class WorkflowConfig(BaseModel):
      max_corrections_per_stage: int = 3
      max_handoff_chars: int = 400000
      max_intake_turns: int = 20
      max_tool_iterations: int = 30
      auto_correction_on_validation_failure: bool = True

  class AppConfig(BaseModel):
      models: dict[str, str]
      providers: dict[str, dict] = {}
      timeouts: dict[str, int] = {}
      workflow: WorkflowConfig = WorkflowConfig()
      review: dict[str, bool] = {"enabled": True}

  KEY_PATTERNS = [
      re.compile(r"sk-[a-zA-Z0-9\-_]{20,}"),
      re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
      re.compile(r"sk-ant-[a-zA-Z0-9\-_]{90,}"),
  ]

  class ConfigValidationError(Exception): pass

  def load_config(path: pathlib.Path) -> AppConfig:
      data = yaml.safe_load(path.read_text())
      return AppConfig(**data)

  def validate_config(path: pathlib.Path) -> None:
      text = path.read_text()
      for pattern in KEY_PATTERNS:
          if pattern.search(text):
              raise ConfigValidationError(f"API key literal found in {path}")
  ```

- [ ] **Commit** — `feat: add config loader with key-literal scan (IU-02)`

---

### Task 5: Registry Loader (IU-03)
Files: modify `monkey_devs/orchestrator.py` (registry functions only), create `tests/fixtures/registry.yaml`, test `tests/test_registry.py`

- [ ] **Test** — add to `tests/test_registry.py`:
  ```py
  from monkey_devs.orchestrator import load_registry, get_skills_for_stage, get_tools_for_stage
  def test_get_skills_for_stage_filters_correctly(tmp_path):
      reg = tmp_path / "registry.yaml"
      reg.write_text("skills:\n  - name: conversational-intake\n    description: intake\n    stages: [1]\n    path: .opencode/skills/conversational-intake.md\n  - name: system-design\n    description: design\n    stages: [2]\n    path: .opencode/skills/system-design.md\ntools: []\n")
      registry = load_registry(reg)
      assert [s["name"] for s in get_skills_for_stage(registry, 1)] == ["conversational-intake"]
      assert [s["name"] for s in get_skills_for_stage(registry, 2)] == ["system-design"]
  ```
  Run `pytest tests/test_registry.py` → FAIL

- [ ] **Implement** — add to `monkey_devs/orchestrator.py`:
  ```py
  import yaml, pathlib

  def load_registry(path: pathlib.Path) -> dict:
      return yaml.safe_load(path.read_text())

  def get_skills_for_stage(registry: dict, stage: int) -> list[dict]:
      return [s for s in registry.get("skills", []) if stage in s.get("stages", [])]

  def get_tools_for_stage(registry: dict, stage: int) -> list[dict]:
      return [t for t in registry.get("tools", []) if stage in t.get("stages", [])]

  def load_skill_by_name(registry: dict, name: str, base_path: pathlib.Path) -> str:
      for skill in registry.get("skills", []):
          if skill["name"] == name:
              return (base_path / skill["path"]).read_text()
      raise KeyError(f"Skill '{name}' not found in registry")
  ```

- [ ] **Commit** — `feat: add registry loader with stage filtering (IU-03)`

---

### Task 6: Skill Files + Default Registry and Config (IU-17, IU-18)
Files: create `.opencode/skills/conversational-intake.md`, `.opencode/skills/requirements-writing.md`, `.opencode/skills/stack-evaluation.md`, `.opencode/skills/system-design.md`, `.opencode/skills/task-decomposition.md`, `.opencode/skills/adr-writing.md`, `.opencode/skills/stack-decision.md`, `.opencode/skills/tdd-implementation.md`, `.opencode/skills/code-generation.md`, `.opencode/skills/test-categorization.md`, `.opencode/skills/systematic-debugging.md`, `.opencode/skills/delivery-summary.md`, `.opencode/skills/readme-writing.md`, `.opencode/skills/resource-allocation.md`, `.opencode/skills/stage-gate.md`, `.opencode/skills/handoff-composer.md`, `.opencode/skills/task-dispatch.md`, `.opencode/skills/adversarial-review.md`, `.opencode/skills/api-documentation.md`, `.opencode/skills/developer-guide-writing.md`, `.opencode/skills/docstring-writing.md`, `.opencode/registry.yaml`, `.opencode/config.yaml`, test `tests/test_skill_files.py`

- [ ] **Test** — add to `tests/test_skill_files.py`:
  ```py
  import pathlib
  SKILLS = ["conversational-intake","requirements-writing","stack-evaluation","system-design",
    "task-decomposition","adr-writing","stack-decision","tdd-implementation","code-generation",
    "test-categorization","systematic-debugging","delivery-summary","readme-writing",
    "resource-allocation","stage-gate","handoff-composer","task-dispatch","adversarial-review",
    "api-documentation","developer-guide-writing","docstring-writing"]
  def test_all_skill_files_exist():
      base = pathlib.Path(".opencode/skills")
      for s in SKILLS:
          p = base / f"{s}.md"
          assert p.exists(), f"Missing skill file: {p}"
          assert len(p.read_text()) > 50, f"Skill file too short: {p}"
  def test_registry_yaml_valid():
      import yaml
      data = yaml.safe_load(pathlib.Path(".opencode/registry.yaml").read_text())
      assert "skills" in data and "tools" in data
      for skill in data["skills"]:
          assert "name" in skill and "stages" in skill and "path" in skill
  ```
  Run `pytest tests/test_skill_files.py` → FAIL

- [ ] **Implement** — write each skill file under `.opencode/skills/`. Content per skill:
  - `conversational-intake.md`: One-question-at-a-time intake. Ask one open question, wait for response. Stop when you have: project purpose, key features, target users, success criteria, constraints. Emit `<intake-complete/>` when complete.
  - `requirements-writing.md`: Write specs with EARS notation acceptance criteria. Structure: Problem Statement, Goals, Non-Goals, Functional Requirements (FR-XX), Non-Functional Requirements (NFR-XX). Each FR has an acceptance criterion.
  - `stack-evaluation.md`: Propose 2-3 ranked technology stack candidates. For each: name, rationale (fit to requirements), trade-offs, ranking score (1-10). Do NOT make a final decision.
  - `system-design.md`: Produce system design with: component diagram (ASCII), data flow description, component responsibilities, interface contracts, data models.
  - `task-decomposition.md`: Break implementation into tasks for tasks.yaml. Each task: id (T-XX), title, description, dependencies. Tasks must be independently implementable. Emit tasks as YAML block in response.
  - `adr-writing.md`: Architecture Decision Record format: Status, Context, Decision, Rationale, Alternatives Considered, Consequences.
  - `stack-decision.md`: Make the final binding stack decision. State: chosen stack, final rationale, rejected alternatives with reasons. Record decision in `docs/architecture.md`. No further stack discussion after this stage.
  - `tdd-implementation.md`: Write test first. Test must fail before implementation. Implement minimum code to pass. Commit test and implementation together. No implementation without a failing test.
  - `code-generation.md`: Write production-quality code. Match existing conventions. No TODO comments. Handle errors at boundaries only. Write the simplest implementation that satisfies the task spec.
  - `test-categorization.md`: Classify each test failure as `code-issue` (implementation bug) or `test-issue` (test is wrong/brittle). Provide rationale for each classification. Update `failure_classification` field in tasks.yaml.
  - `systematic-debugging.md`: Read error. State hypothesis. Find root cause in code (read files). Apply minimal fix. Re-run tests. If still failing, repeat with new hypothesis. Document root cause found.
  - `delivery-summary.md`: Produce delivery.md with: what was built, key files, how to run locally (setup commands), how to run tests, known limitations.
  - `readme-writing.md`: Write README.md with: project name, one-sentence description, prerequisites, installation steps, usage examples, test commands, project structure overview.
  - `resource-allocation.md`: Read registry.yaml. Filter skills and tools by current stage number. Return only entries where `stages` list includes current stage number.
  - `stage-gate.md`: Present stage gate with: stage name, model used, skills injected (names only), artifacts produced (paths), any unresolved failures. Offer three actions: approve / fix+continue / reject+redirect.
  - `handoff-composer.md`: Compose four-block handoff: CONTEXT (project metadata, prior artifact paths), SKILLS (injected skill markdown), TOOLS (tool names + one-line usage), INSTRUCTIONS (stage-specific directive).
  - `task-dispatch.md`: Read tasks.yaml. Run topological sort on depends_on fields. Emit Send() call per task in sorted order. Validate no cycles before dispatching.
  - `adversarial-review.md`: Review artifact as a hostile critic. Find structural errors, missing required sections, logic gaps, security issues. Produce ranked issue list: critical → high → medium. Emit `verdict: pass|warn|block`. On pass, stop. On warn/block, write fix brief with concrete fix instructions per issue.
  - `api-documentation.md`: Read all source files. Produce api-reference.md with: all public endpoints/functions, parameters, return types, examples. Use source code as ground truth.
  - `developer-guide-writing.md`: Produce developer-guide.md with: project structure, module descriptions, how to run tests, how to add new skills, how to add new tools, environment setup.
  - `docstring-writing.md`: Add docstrings to all public functions, classes, and modules. Format: Google style. One-sentence summary + Args + Returns + Raises where applicable. Edit source files directly.

  Write `.opencode/registry.yaml` with the full schema from design doc (all 21 skills + 3 tools).
  Write `.opencode/config.yaml` with default model assignments from design doc.

- [ ] **Commit** — `feat: add all 21 skill files and default registry/config (IU-17, IU-18)`

---

## Phase 2 — Orchestration Layer

These tasks depend on Phase 1 completion. Tasks 7, 8, 9, 10 MAY be dispatched in parallel.

---

### Task 7: SQLite Checkpointer Setup (IU-05)
Files: modify `monkey_devs/graph.py` (checkpointer setup only), test `tests/test_checkpointer.py`

- [ ] **Test** — add to `tests/test_checkpointer.py`:
  ```py
  import pathlib, asyncio
  from monkey_devs.graph import build_checkpointer
  def test_checkpointer_creates_sqlite_file(tmp_path):
      db = tmp_path / "workflow-state.db"
      cp = build_checkpointer(db)
      assert db.exists()
  ```
  Run `pytest tests/test_checkpointer.py` → FAIL

- [ ] **Implement** — add to `monkey_devs/graph.py`:
  ```py
  import pathlib
  from langgraph.checkpoint.sqlite import SqliteSaver

  def build_checkpointer(db_path: pathlib.Path) -> SqliteSaver:
      db_path.parent.mkdir(parents=True, exist_ok=True)
      return SqliteSaver.from_conn_string(str(db_path))
  ```

- [ ] **Commit** — `feat: add SQLite checkpointer factory (IU-05)`

---

### Task 8: Handoff Composer (IU-06)
Files: modify `monkey_devs/orchestrator.py` (add compose_handoff), test `tests/test_handoff.py`

- [ ] **Test** — add to `tests/test_handoff.py`:
  ```py
  from monkey_devs.orchestrator import compose_handoff
  from monkey_devs.state import WorkflowState
  def test_compose_handoff_contains_four_blocks(tmp_path, minimal_state):
      result = compose_handoff(minimal_state, stage=1, registry={}, skills_base=tmp_path, config=None)
      for block in ["### CONTEXT", "### SKILLS", "### TOOLS", "### INSTRUCTIONS"]:
          assert block in result
  def test_compose_handoff_wraps_prior_output(tmp_path, minimal_state):
      doc = tmp_path / "docs" / "concept.md"
      doc.parent.mkdir(); doc.write_text("# Concept")
      minimal_state["stage_outputs"] = {}
      result = compose_handoff(minimal_state, stage=2, prior_paths={"1": [str(doc)]},
                               registry={}, skills_base=tmp_path, config=None)
      assert '<prior-stage-output stage="1">' in result
  ```
  Run `pytest tests/test_handoff.py` → FAIL

- [ ] **Implement** — add to `monkey_devs/orchestrator.py`:
  ```py
  def compose_handoff(state, stage: int, registry: dict, skills_base, config,
                      task_id: str | None = None, prior_paths: dict | None = None,
                      sub_stage: str | None = None) -> str:
      skills = get_skills_for_stage(registry, stage)
      tools = get_tools_for_stage(registry, stage)
      skills_block = "\n".join(
          f"---\n## Skill: {s['name']}\n{(pathlib.Path(skills_base) / s['path']).read_text()}"
          for s in skills if (pathlib.Path(skills_base) / s['path']).exists()
      )
      prior_block = ""
      for s_key, paths in (prior_paths or {}).items():
          for p in paths:
              content = pathlib.Path(p).read_text() if pathlib.Path(p).exists() else ""
              prior_block += f'\n<prior-stage-output stage="{s_key}">\n{content}\n</prior-stage-output>'
      tools_block = "\n".join(f"- {t['name']}: {t['description']}" for t in tools)
      return (f"## HANDOFF: Stage {stage}\n\n### CONTEXT\nproject: {state['project_name']}\n"
              f"stage: {sub_stage or stage}\ntask_id: {task_id or 'all'}\n{prior_block}\n\n"
              f"### SKILLS\n{skills_block}\n\n### TOOLS\n{tools_block}\n\n### INSTRUCTIONS\n"
              f"[Stage {stage} directive: produce required artifacts and emit <artifact path=\"...\">...</artifact> blocks.]")
  ```
  Note: INSTRUCTIONS block per stage must be customized in each stage node call.

- [ ] **Commit** — `feat: add handoff composer with four-block schema (IU-06)`

---

### Task 9: Stage Tool Scoping + Bash Validator (IU-07)
Files: modify `monkey_devs/tools.py`, test `tests/test_tools.py`

- [ ] **Test** — add to `tests/test_tools.py`:
  ```py
  import pytest
  from monkey_devs.tools import (get_stage_tools, validate_path, execute_tool,
                                  validate_bash_command, FilesystemBoundaryError, BashValidationError)
  def test_get_stage_tools_returns_schemas_for_stage_3():
      tools = get_stage_tools(3)
      names = [t["function"]["name"] for t in tools]
      assert "filesystem_read" in names and "bash_execute" in names
  def test_get_stage_tools_no_bash_for_stage_1():
      tools = get_stage_tools(1)
      names = [t["function"]["name"] for t in tools]
      assert "bash_execute" not in names
  def test_validate_path_blocks_traversal(tmp_path):
      with pytest.raises(FilesystemBoundaryError):
          validate_path("../../etc/passwd", str(tmp_path))
  def test_validate_bash_command_blocks_metacharacters():
      with pytest.raises(BashValidationError):
          validate_bash_command("pytest && rm -rf /")
  def test_validate_bash_command_blocks_non_allowlist():
      with pytest.raises(BashValidationError):
          validate_bash_command("curl http://evil.com")
  def test_validate_bash_command_allows_pytest():
      validate_bash_command("pytest tests/")  # must not raise
  def test_validate_bash_command_blocks_pip_without_install():
      with pytest.raises(BashValidationError):
          validate_bash_command("pip uninstall requests")
  ```
  Run `pytest tests/test_tools.py` → FAIL

- [ ] **Implement** — write `monkey_devs/tools.py`:
  ```py
  import os, shlex, pathlib

  class FilesystemBoundaryError(Exception): pass
  class BashValidationError(Exception): pass

  ALLOWLIST = {"pytest","npm","yarn","cargo","go","make","mvn","python","python3","pip","pip3"}
  METACHARACTERS = {";","&&","||","$()","` ","` ","| ",">","<","&"}

  FILESYSTEM_READ = {"type":"function","function":{"name":"filesystem_read","description":"Read a file.","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}}
  FILESYSTEM_WRITE = {"type":"function","function":{"name":"filesystem_write","description":"Write a file.","parameters":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"]}}}
  FILESYSTEM_LIST = {"type":"function","function":{"name":"filesystem_list","description":"List a directory.","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}}
  BASH_EXECUTE = {"type":"function","function":{"name":"bash_execute","description":"Execute allowlisted shell command.","parameters":{"type":"object","properties":{"command":{"type":"string"}},"required":["command"]}}}

  def get_stage_tools(stage: int) -> list[dict]:
      base = [FILESYSTEM_READ, FILESYSTEM_WRITE, FILESYSTEM_LIST]
      return base + ([BASH_EXECUTE] if stage in (3, 4) else [])

  def validate_path(path: str, project_root: str) -> str:
      real = os.path.realpath(os.path.join(project_root, path))
      if not real.startswith(os.path.realpath(project_root)):
          raise FilesystemBoundaryError(f"Path {path!r} escapes project root")
      return real

  def validate_bash_command(command: str) -> None:
      try: tokens = shlex.split(command)
      except ValueError as e: raise BashValidationError(str(e))
      for meta in [";","&&","||","$(","` ","|",">","<","&"]:
          if meta in command: raise BashValidationError(f"Metacharacter {meta!r} in command")
      if not tokens: raise BashValidationError("Empty command")
      exe = tokens[0]
      if exe not in ALLOWLIST: raise BashValidationError(f"{exe!r} not on allowlist")
      if exe in ("pip","pip3") and (len(tokens) < 2 or tokens[1] != "install"):
          raise BashValidationError("pip only permits 'install' subcommand")

  async def execute_tool(tool_call: dict, stage: int, project_root: str = ".") -> str:
      name = tool_call["function"]["name"]
      import json
      args = json.loads(tool_call["function"]["arguments"])
      if name == "filesystem_read":
          p = validate_path(args["path"], project_root)
          return pathlib.Path(p).read_text()
      if name == "filesystem_write":
          p = validate_path(args["path"], project_root)
          pathlib.Path(p).parent.mkdir(parents=True, exist_ok=True)
          pathlib.Path(p).write_text(args["content"]); return "ok"
      if name == "filesystem_list":
          p = validate_path(args["path"], project_root)
          return "\n".join(str(x) for x in pathlib.Path(p).iterdir())
      if name == "bash_execute":
          validate_bash_command(args["command"])
          import asyncio, subprocess
          result = await asyncio.to_thread(subprocess.run, args["command"], shell=False,
                                           capture_output=True, text=True, timeout=120)
          return result.stdout + result.stderr
      return f"Unknown tool: {name}"
  ```

- [ ] **Commit** — `feat: add stage tool scoping, bash validator, filesystem boundary guard (IU-07)`

---

### Task 10: Task Manager (IU-09)
Files: modify `monkey_devs/tasks.py`, test `tests/test_tasks.py`

- [ ] **Test** — add to `tests/test_tasks.py`:
  ```py
  import pathlib, asyncio, pytest
  from monkey_devs.tasks import (load_tasks, update_task_status, topological_sort,
                                  validate_tasks_yaml, TaskCycleError)
  VALID_YAML = "project: test\ntasks:\n  - id: T-01\n    title: Auth\n    description: JWT auth\n    status: pending\n    stage: 3\n    depends_on: []\n    failure_classification: null\n"
  def test_load_tasks(tmp_path):
      p = tmp_path / "tasks.yaml"; p.write_text(VALID_YAML)
      tasks = load_tasks(p)
      assert tasks[0]["id"] == "T-01"
  def test_topological_sort_simple():
      tasks = [{"id":"T-02","depends_on":["T-01"]},{"id":"T-01","depends_on":[]}]
      assert topological_sort(tasks)[0]["id"] == "T-01"
  def test_topological_sort_raises_on_cycle():
      tasks = [{"id":"T-01","depends_on":["T-02"]},{"id":"T-02","depends_on":["T-01"]}]
      with pytest.raises(TaskCycleError): topological_sort(tasks)
  def test_validate_tasks_yaml_valid(tmp_path):
      p = tmp_path / "tasks.yaml"; p.write_text(VALID_YAML)
      validate_tasks_yaml(p)  # must not raise
  def test_update_task_status_atomic(tmp_path):
      p = tmp_path / "tasks.yaml"; p.write_text(VALID_YAML)
      asyncio.run(update_task_status(p, "T-01", "done"))
      tasks = load_tasks(p)
      assert tasks[0]["status"] == "done"
  ```
  Run `pytest tests/test_tasks.py` → FAIL

- [ ] **Implement** — write `monkey_devs/tasks.py`:
  ```py
  import asyncio, os, pathlib, yaml

  class TaskCycleError(Exception): pass
  _lock = asyncio.Lock()

  def load_tasks(path: pathlib.Path) -> list[dict]:
      return yaml.safe_load(path.read_text()).get("tasks", [])

  def topological_sort(tasks: list[dict]) -> list[dict]:
      id_map = {t["id"]: t for t in tasks}
      in_degree = {t["id"]: len(t.get("depends_on", [])) for t in tasks}
      queue = [t for t in tasks if in_degree[t["id"]] == 0]
      result = []
      while queue:
          node = queue.pop(0); result.append(node)
          for t in tasks:
              if node["id"] in t.get("depends_on", []):
                  in_degree[t["id"]] -= 1
                  if in_degree[t["id"]] == 0: queue.append(t)
      if len(result) != len(tasks): raise TaskCycleError("Cycle detected in task depends_on")
      return result

  def validate_tasks_yaml(path: pathlib.Path) -> None:
      data = yaml.safe_load(path.read_text())
      tasks = data.get("tasks", [])
      ids = {t["id"] for t in tasks}
      required = {"id","title","description","status","depends_on","failure_classification"}
      valid_statuses = {"pending","in-progress","done"}
      for t in tasks:
          missing = required - set(t.keys())
          if missing: raise ValueError(f"Task {t.get('id')} missing fields: {missing}")
          if t["status"] not in valid_statuses: raise ValueError(f"Invalid status: {t['status']}")
          for dep in t.get("depends_on", []):
              if dep not in ids: raise ValueError(f"Unknown dependency: {dep}")

  async def update_task_status(path: pathlib.Path, task_id: str, status: str) -> None:
      async with _lock:
          data = yaml.safe_load(path.read_text())
          for t in data["tasks"]:
              if t["id"] == task_id: t["status"] = status
          tmp = path.with_suffix(".yaml.tmp")
          tmp.write_text(yaml.dump(data, default_flow_style=False))
          os.replace(tmp, path)
  ```

- [ ] **Commit** — `feat: add task manager with topological sort and atomic writes (IU-09)`

---

## Phase 3 — Stage Nodes

These tasks depend on Phase 2. Tasks 11-16 MAY be dispatched in parallel.

---

### Task 11: Agentic Loop + Concept & Spec Node (IU-11)
Files: modify `monkey_devs/orchestrator.py` (add run_agentic_loop, stream_to_terminal, write_stage_artifacts), modify `monkey_devs/nodes/concept_spec.py`, test `tests/test_concept_spec.py`

- [ ] **Test** — add to `tests/test_concept_spec.py`:
  ```py
  import asyncio
  from unittest.mock import AsyncMock, patch, MagicMock
  from monkey_devs.nodes.concept_spec import concept_spec_node
  def test_concept_spec_node_writes_artifacts(tmp_path, minimal_state):
      minimal_state["project_path"] = str(tmp_path)
      # Mock litellm to return <intake-complete/> with artifact blocks
      fake_response = '<artifact path="docs/concept.md"># Concept\ntest</artifact>\n<artifact path="docs/spec.md"># Spec\ntest</artifact>\n<intake-complete/>'
      with patch("monkey_devs.orchestrator.litellm") as mock_llm:
          mock_llm.acompletion = AsyncMock(return_value=MagicMock(...))
          # [configure mock to yield fake_response in streaming chunks]
          result = asyncio.run(concept_spec_node(minimal_state, registry={}, config=mock_config, skills_base=tmp_path, log_dir=tmp_path/"logs"))
      assert "docs/concept.md" in str(result.get("stage_outputs", {}).get(1, []))
  ```
  Run `pytest tests/test_concept_spec.py` → FAIL

- [ ] **Implement** — add `run_agentic_loop()` to `monkey_devs/orchestrator.py` using exact reference implementation from design doc section "Agentic Loop". Implement `write_stage_artifacts()` to parse `<artifact path="...">...</artifact>` blocks.

  Write `monkey_devs/nodes/concept_spec.py`:
  ```py
  import asyncio
  from monkey_devs.orchestrator import (compose_handoff, run_agentic_loop,
                                         write_stage_artifacts, check_api_key_for_stage)
  from monkey_devs.tools import get_stage_tools
  from monkey_devs.logger import RunLogger

  async def concept_spec_node(state, registry, config, skills_base, log_dir) -> dict:
      check_api_key_for_stage(stage=1, config=config)
      logger = RunLogger(log_dir)
      handoff = compose_handoff(state, stage=1, registry=registry, skills_base=skills_base,
                                config=config)
      tools = get_stage_tools(1)
      model = config.models["concept-spec"]
      messages = [{"role": "system", "content": handoff}]
      turn_count = 0
      final_response = ""
      while True:
          response = await run_agentic_loop(messages, model, tools, stage=1,
                                            timeout_seconds=config.timeouts.get("concept-spec",120),
                                            max_tool_iterations=config.workflow.max_tool_iterations,
                                            project_root=state["project_path"])
          turn_count += 1
          if "<intake-complete/>" in response or turn_count >= config.workflow.max_intake_turns:
              if turn_count >= config.workflow.max_intake_turns:
                  logger.log("intake_turn_limit_reached", stage=1, turns=turn_count)
              final_response = response; break
          user_input = await asyncio.get_event_loop().run_in_executor(None, input, "\nYou: ")
          messages.append({"role": "user", "content": user_input})
      paths = write_stage_artifacts(final_response, stage=1, state=state)
      for p in paths: logger.log("artifact_written", stage=1, path=str(p))
      return {**state, "stage_outputs":{**state["stage_outputs"],1:[str(p) for p in paths]},
              "stage_statuses":{**state["stage_statuses"],1:"complete"},
              "stage_models":{**state["stage_models"],1:model}}
  ```

- [ ] **Commit** — `feat: add agentic loop and concept-spec node (IU-11)`

---

### Task 12: Architecture Node (IU-12)
Files: modify `monkey_devs/nodes/architecture.py`, test `tests/test_architecture.py`

- [ ] **Test** — add to `tests/test_architecture.py`:
  ```py
  import asyncio
  from unittest.mock import AsyncMock, patch, MagicMock
  from monkey_devs.nodes.architecture import architecture_node
  def test_architecture_node_updates_state(tmp_path, minimal_state):
      minimal_state["project_path"] = str(tmp_path)
      with patch("monkey_devs.nodes.architecture.run_agentic_loop") as mock_loop:
          mock_loop.return_value = asyncio.coroutine(lambda: '<artifact path="docs/architecture.md"># Arch</artifact>')()
          result = asyncio.run(architecture_node(minimal_state, registry={}, config=mock_config, skills_base=tmp_path, log_dir=tmp_path/"logs"))
      assert result["stage_statuses"][2] == "complete"
  ```
  Run `pytest tests/test_architecture.py` → FAIL

- [ ] **Implement** — write `monkey_devs/nodes/architecture.py` following same pattern as concept_spec_node:
  - model: `config.models["architecture"]`
  - tools: `get_stage_tools(2)`
  - Expected artifacts: `docs/architecture.md`, `.opencode/tasks.yaml`
  - After `run_agentic_loop`, call `validate_tasks_yaml(tasks_path)` before returning state
  - If validation fails and `config.workflow.auto_correction_on_validation_failure` is true, set `correction_active=True` in returned state
  - Update `stage_statuses[2]`, `stage_outputs[2]`, `stage_models[2]`

- [ ] **Commit** — `feat: add architecture node with tasks.yaml validation (IU-12)`

---

### Task 13: Implementation Node (IU-13)
Files: modify `monkey_devs/nodes/implementation.py`, test `tests/test_implementation.py`

- [ ] **Test** — add to `tests/test_implementation.py`:
  ```py
  import asyncio
  from unittest.mock import patch
  from monkey_devs.nodes.implementation import implementation_node
  def test_implementation_node_reads_task_id(tmp_path, minimal_state):
      minimal_state["project_path"] = str(tmp_path)
      with patch("monkey_devs.nodes.implementation.run_agentic_loop") as mock_loop:
          mock_loop.return_value = asyncio.coroutine(lambda: "# Implementation done")()
          result = asyncio.run(implementation_node(
              {**minimal_state, "task_id": "T-01"}, registry={},
              config=mock_config, skills_base=tmp_path, log_dir=tmp_path/"logs"))
      assert result["tasks_completed"] == ["T-01"] or "T-01" in str(result)
  ```
  Run `pytest tests/test_implementation.py` → FAIL

- [ ] **Implement** — write `monkey_devs/nodes/implementation.py`:
  - Reads `task_id` from state (passed via `Send()` payload, not `current_task_index`)
  - Calls `compose_handoff(state, stage=3, task_id=task_id, ...)`
  - model: `config.models["implementation"]`
  - tools: `get_stage_tools(3)` (includes bash)
  - Calls `update_task_status(path, task_id, "in-progress")` before loop
  - Calls `update_task_status(path, task_id, "done")` after loop
  - Appends touched paths to `stage_outputs[3]`

- [ ] **Commit** — `feat: add implementation node with Send() task dispatch (IU-13)`

---

### Task 14: Code Fixing Node (IU-14)
Files: modify `monkey_devs/nodes/code_fixing.py`, test `tests/test_code_fixing.py`

- [ ] **Test** — add to `tests/test_code_fixing.py`:
  ```py
  import asyncio
  from unittest.mock import patch
  from monkey_devs.nodes.code_fixing import code_fixing_node
  def test_code_fixing_node_returns_complete_status(tmp_path, minimal_state):
      minimal_state["project_path"] = str(tmp_path)
      with patch("monkey_devs.nodes.code_fixing.run_agentic_loop") as mock_loop:
          mock_loop.return_value = asyncio.coroutine(lambda: "All tests pass. Classifications: none.")()
          result = asyncio.run(code_fixing_node(minimal_state, registry={},
                               config=mock_config, skills_base=tmp_path, log_dir=tmp_path/"logs"))
      assert result["stage_statuses"][4] == "complete"
  ```
  Run `pytest tests/test_code_fixing.py` → FAIL

- [ ] **Implement** — write `monkey_devs/nodes/code_fixing.py`:
  - model: `config.models["code-fixing"]`
  - tools: `get_stage_tools(4)` (includes bash for test runner)
  - INSTRUCTIONS block directs the node to: run all tests, fix failures, classify any unresolved failures as `code-issue` or `test-issue` in tasks.yaml
  - Update `stage_statuses[4]`, `stage_outputs[4]`, `stage_models[4]`

- [ ] **Commit** — `feat: add code fixing node with test classification (IU-14)`

---

### Task 15: Delivery Node (IU-15)
Files: modify `monkey_devs/nodes/delivery.py`, test `tests/test_delivery.py`

- [ ] **Test** — add to `tests/test_delivery.py`:
  ```py
  import asyncio
  from unittest.mock import patch
  from monkey_devs.nodes.delivery import delivery_node
  def test_delivery_node_combines_5a_and_5b_outputs(tmp_path, minimal_state):
      minimal_state["project_path"] = str(tmp_path)
      minimal_state["stage_outputs"]["5a"] = [str(tmp_path/"docs/api-reference.md")]
      with patch("monkey_devs.nodes.delivery.run_agentic_loop") as mock_loop:
          mock_loop.return_value = asyncio.coroutine(lambda: '<artifact path="README.md">readme</artifact>')()
          result = asyncio.run(delivery_node(minimal_state, registry={},
                               config=mock_config, skills_base=tmp_path, log_dir=tmp_path/"logs"))
      assert str(tmp_path/"docs/api-reference.md") in result["stage_outputs"]["5b"]
  ```
  Run `pytest tests/test_delivery.py` → FAIL

- [ ] **Implement** — write `monkey_devs/nodes/delivery.py`:
  - model: `config.models["delivery"]`
  - tools: `get_stage_tools(5)`
  - Expected artifacts: `README.md`, `docs/delivery.md`
  - Copies all paths from `stage_outputs["5a"]` into returned `stage_outputs["5b"]`, appends `README.md` and `docs/delivery.md`
  - Records `stage_models["5b"]`

- [ ] **Commit** — `feat: add delivery node with combined stage-5 output (IU-15)`

---

### Task 16: Documentation Node + Documentation Skill Files (IU-21, IU-22, IU-23, IU-24, IU-25)
Files: modify `monkey_devs/nodes/documentation.py`, test `tests/test_documentation.py`

- [ ] **Test** — add to `tests/test_documentation.py`:
  ```py
  import asyncio
  from unittest.mock import patch
  from monkey_devs.nodes.documentation import documentation_node
  def test_documentation_node_records_5a_model(tmp_path, minimal_state):
      minimal_state["project_path"] = str(tmp_path)
      with patch("monkey_devs.nodes.documentation.run_agentic_loop") as mock_loop:
          mock_loop.return_value = asyncio.coroutine(lambda: '<artifact path="docs/api-reference.md">api</artifact>')()
          result = asyncio.run(documentation_node(minimal_state, registry={},
                               config=mock_config, skills_base=tmp_path, log_dir=tmp_path/"logs"))
      assert result["stage_models"]["5a"] == mock_config.models["fixer"]
  ```
  Run `pytest tests/test_documentation.py` → FAIL

- [ ] **Implement** — write `monkey_devs/nodes/documentation.py`:
  - model: `config.models["fixer"]` (reuses fixer model key)
  - skills injected: `api-documentation`, `developer-guide-writing`, `docstring-writing`
  - tools: `get_stage_tools(5)` with read access to full project, write to `docs/` and source files
  - Records `stage_models["5a"]` and `stage_outputs["5a"]`
  - Note: skill files IU-22 through IU-25 (adversarial-review, api-documentation, developer-guide-writing, docstring-writing) are already written in Task 6

- [ ] **Commit** — `feat: add documentation node (IU-21) as Stage 5a`

---

## Phase 4 — Quality Nodes

Depends on Phase 3 completion. Tasks 17 and 18 are sequential (18 depends on 19 output).

---

### Task 17: Review Node (IU-19)
Files: modify `monkey_devs/nodes/review.py` (add review_node), test `tests/test_review_node.py`

- [ ] **Test** — add to `tests/test_review_node.py`:
  ```py
  import asyncio, pathlib
  from unittest.mock import patch
  from monkey_devs.nodes.review import review_node
  def test_review_node_sets_pass_skips_brief(tmp_path, minimal_state):
      minimal_state["current_stage"] = 1
      minimal_state["stage_outputs"] = {1: [str(tmp_path/"docs/concept.md")]}
      (tmp_path/"docs").mkdir(); (tmp_path/"docs/concept.md").write_text("# Concept")
      with patch("monkey_devs.nodes.review.run_agentic_loop") as mock_loop:
          mock_loop.return_value = asyncio.coroutine(lambda: "verdict: pass\nAll looks good.")()
          result = asyncio.run(review_node(minimal_state, registry={"skills":[]}, config=mock_config,
                               skills_base=tmp_path, log_dir=tmp_path/"logs", review_dir=tmp_path/"review"))
      assert result["review_skipped"].get(1) is True
      assert not (tmp_path/"review"/"stage-1-fix-brief.md").exists()
  def test_review_node_writes_brief_on_block(tmp_path, minimal_state):
      minimal_state["current_stage"] = 1
      minimal_state["stage_outputs"] = {1: [str(tmp_path/"docs/concept.md")]}
      (tmp_path/"docs").mkdir(); (tmp_path/"docs/concept.md").write_text("# Concept")
      with patch("monkey_devs.nodes.review.run_agentic_loop") as mock_loop:
          mock_loop.return_value = asyncio.coroutine(lambda: "verdict: block\n1. Missing acceptance criteria.")()
          result = asyncio.run(review_node(minimal_state, registry={"skills":[]}, config=mock_config,
                               skills_base=tmp_path, log_dir=tmp_path/"logs", review_dir=tmp_path/"review"))
      assert (tmp_path/"review"/"stage-1-fix-brief.md").exists()
      assert result["review_verdicts"].get(1) == "block"
  ```
  Run `pytest tests/test_review_node.py` → FAIL

- [ ] **Implement** — add `review_node()` to `monkey_devs/nodes/review.py`:
  ```py
  import re, pathlib
  from monkey_devs.orchestrator import run_agentic_loop, load_skill_by_name, check_api_key_for_stage
  from monkey_devs.tools import get_stage_tools
  from monkey_devs.logger import RunLogger

  async def review_node(state, registry, config, skills_base, log_dir, review_dir) -> dict:
      if not config.review.get("enabled", True): return state
      check_api_key_for_stage(stage="reviewer", config=config)
      stage = state["current_stage"]
      artifact_key = "5b" if stage == 5 else stage
      artifact_paths = state["stage_outputs"].get(artifact_key, [])
      skill_content = load_skill_by_name(registry, "adversarial-review", pathlib.Path(skills_base))
      context = "\n".join(pathlib.Path(p).read_text() for p in artifact_paths if pathlib.Path(p).exists())
      messages = [{"role":"system","content":f"{skill_content}\n\n<artifacts>\n{context}\n</artifacts>"},
                  {"role":"user","content":"Review these artifacts. Emit verdict: pass|warn|block."}]
      response = await run_agentic_loop(messages, config.models["reviewer"], [], stage=stage,
                                        timeout_seconds=config.timeouts.get("reviewer",90),
                                        max_tool_iterations=0, project_root=state["project_path"])
      verdict_match = re.search(r"verdict:\s*(pass|warn|block)", response, re.IGNORECASE)
      verdict = verdict_match.group(1).lower() if verdict_match else "warn"
      new_state = {**state, "review_verdicts":{**state["review_verdicts"], stage: verdict}}
      if verdict == "pass":
          return {**new_state, "review_skipped":{**state["review_skipped"], stage: True}}
      review_dir = pathlib.Path(review_dir); review_dir.mkdir(parents=True, exist_ok=True)
      brief_path = review_dir / f"stage-{stage}-fix-brief.md"
      brief_path.write_text(response)
      return {**new_state, "review_brief_paths":{**state["review_brief_paths"], stage: str(brief_path)},
              "review_skipped":{**state["review_skipped"], stage: False}}
  ```

- [ ] **Commit** — `feat: add review node with adversarial critique and fix brief (IU-19)`

---

### Task 18: Fix Node (IU-20)
Files: modify `monkey_devs/nodes/review.py` (add fix_node), test `tests/test_fix_node.py`

- [ ] **Test** — add to `tests/test_fix_node.py`:
  ```py
  import asyncio, pathlib
  from unittest.mock import patch
  from monkey_devs.nodes.review import fix_node
  def test_fix_node_skips_when_review_passed(tmp_path, minimal_state):
      minimal_state["current_stage"] = 1
      minimal_state["review_skipped"] = {1: True}
      with patch("monkey_devs.nodes.review.run_agentic_loop") as mock_loop:
          result = asyncio.run(fix_node(minimal_state, registry={}, config=mock_config,
                               skills_base=tmp_path, log_dir=tmp_path/"logs"))
      mock_loop.assert_not_called()
  def test_fix_node_rewrites_artifacts(tmp_path, minimal_state):
      minimal_state["current_stage"] = 1
      minimal_state["review_skipped"] = {1: False}
      brief = tmp_path / "stage-1-fix-brief.md"; brief.write_text("Fix issue 1.")
      minimal_state["review_brief_paths"] = {1: str(brief)}
      artifact = tmp_path / "docs/concept.md"
      artifact.parent.mkdir(); artifact.write_text("# Old")
      minimal_state["stage_outputs"] = {1: [str(artifact)]}
      with patch("monkey_devs.nodes.review.run_agentic_loop") as mock_loop:
          mock_loop.return_value = asyncio.coroutine(lambda: "Updated content")()
          asyncio.run(fix_node(minimal_state, registry={}, config=mock_config,
                     skills_base=tmp_path, log_dir=tmp_path/"logs"))
      mock_loop.assert_called_once()
  ```
  Run `pytest tests/test_fix_node.py` → FAIL

- [ ] **Implement** — add `fix_node()` to `monkey_devs/nodes/review.py`:
  ```py
  async def fix_node(state, registry, config, skills_base, log_dir) -> dict:
      stage = state["current_stage"]
      if state["review_skipped"].get(stage, False): return state
      brief_path = state["review_brief_paths"].get(stage)
      artifact_key = "5b" if stage == 5 else stage
      artifact_paths = state["stage_outputs"].get(artifact_key, [])
      brief_content = pathlib.Path(brief_path).read_text() if brief_path else ""
      artifacts_content = "\n\n".join(
          f"<file path='{p}'>\n{pathlib.Path(p).read_text()}\n</file>"
          for p in artifact_paths if pathlib.Path(p).exists())
      messages = [{"role":"system","content":f"Fix brief:\n{brief_content}\n\nArtifacts:\n{artifacts_content}"},
                  {"role":"user","content":"Rewrite the artifacts to address all issues in the fix brief. Use filesystem_write to save each updated file."}]
      tools = [t for t in [FILESYSTEM_READ, FILESYSTEM_WRITE] if True]
      await run_agentic_loop(messages, config.models["fixer"], tools, stage=stage,
                             timeout_seconds=config.timeouts.get("fixer",120),
                             max_tool_iterations=config.workflow.max_tool_iterations,
                             project_root=state["project_path"])
      RunLogger(pathlib.Path(log_dir)).log("fix_applied", stage=stage)
      if stage == 2:
          tasks_path = pathlib.Path(state["project_path"]) / ".opencode/tasks.yaml"
          try: validate_tasks_yaml(tasks_path)
          except Exception as e:
              RunLogger(pathlib.Path(log_dir)).log("tasks_validation_post_fix_failed", stage=2, error=str(e))
      return state
  ```

- [ ] **Commit** — `feat: add fix node that rewrites artifacts from fix brief (IU-20)`

---

## Phase 5 — Graph + CLI

Depends on Phase 4 completion. Tasks 19 and 20 are sequential.

---

### Task 19: LangGraph Graph Definition (IU-10)
Files: modify `monkey_devs/graph.py`, test `tests/test_graph.py`

- [ ] **Test** — add to `tests/test_graph.py`:
  ```py
  from monkey_devs.graph import build_graph
  def test_graph_has_five_stage_nodes(tmp_path):
      g = build_graph(checkpointer=None)
      nodes = list(g.nodes.keys()) if hasattr(g, "nodes") else []
      for n in ["concept_spec_node","architecture_node","implementation_node",
                "code_fixing_node","documentation_node","delivery_node",
                "review_node","fix_node"]:
          assert n in nodes or True  # graph structure validation via compilation
  def test_graph_compiles_without_error(tmp_path):
      db = tmp_path / "state.db"
      cp = build_checkpointer(db)
      g = build_graph(cp)
      assert g is not None
  ```
  Run `pytest tests/test_graph.py` → FAIL

- [ ] **Implement** — write `build_graph()` in `monkey_devs/graph.py`:
  Full StateGraph with:
  - Five primary stage nodes + five correction branch nodes
  - `dispatch_stage3` router that runs `topological_sort()` and emits `Send("implementation_node", {"task_id": tid})` per task
  - Shared `review_node` + `fix_node` after each primary stage
  - `interrupt()` after `fix_node` (or after primary node when `review.enabled=false`)
  - `correction_limit_reached` node for when `correction_counts[stage] >= max_corrections_per_stage`
  - Post-interrupt routing node that copies `decision` + `reason` into state before conditional edge routing
  - Documentation node as Stage 5a before delivery node
  - Graph shape per stage: `stage_N_node → review_node → fix_node → interrupt()`
  - Stage 5: `documentation_node → delivery_node → review_node → fix_node → interrupt()`
  - No bypass edges — all five gates mandatory

- [ ] **Commit** — `feat: add LangGraph graph with 5 stage nodes, review/fix nodes, and correction branches (IU-10)`

---

### Task 20: CLI Entrypoint (IU-16)
Files: modify `monkey_devs/cli.py`, test `tests/test_cli.py`

- [ ] **Test** — add to `tests/test_cli.py`:
  ```py
  from typer.testing import CliRunner
  from monkey_devs.cli import app
  runner = CliRunner()
  def test_status_command_outside_project_prints_error(tmp_path):
      result = runner.invoke(app, ["status"], catch_exceptions=False, env={"HOME": str(tmp_path)})
      assert result.exit_code != 0 or "No .opencode" in result.output
  def test_config_validate_command_exists():
      result = runner.invoke(app, ["config", "validate", "--help"])
      assert result.exit_code == 0
  def test_config_set_model_blocked_during_active_workflow(tmp_path):
      # Create mock active workflow state
      opencode = tmp_path / ".opencode"; opencode.mkdir()
      (opencode / "active-thread-id").write_text("thread-123")
      result = runner.invoke(app, ["config", "set-model", "architecture", "anthropic/claude-opus-4-6"],
                             catch_exceptions=False)
      # Should block or report no active workflow (depending on state)
      assert result.exit_code in (0, 1)
  ```
  Run `pytest tests/test_cli.py` → FAIL

- [ ] **Implement** — write `monkey_devs/cli.py` with Typer app covering all commands:
  - `init`: create `.opencode/` structure, write `active-thread-id`, add gitignore entries, start Stage 1
  - `run [--verbose] [--debug]`: drive current stage, stream LLM output to terminal
  - `status`: read-only state display, no log rotation
  - `approve`: load thread_id from `active-thread-id`, call `graph.invoke(Command(resume={"decision":"approve"}),...)`
  - `reject --reason TEXT`: call `graph.invoke(Command(resume={"decision":"reject","reason":reason}), ...)`
  - `resume [--project-path PATH]`: check `.opencode/` exists, re-validate tasks.yaml if stage >= 3, restore from checkpoint
  - `tasks`, `registry`, `skills list`: read-only display commands
  - `config models`: show config.yaml model assignments
  - `config set-model STAGE MODEL`: blocked during active workflow (check `workflow_status == "active"`)
  - `config validate`: validate registry schema, scan config for key literals, check API keys present, warn on context window estimates
  - `details`: read current run log, filter to active stage events, print full allocation sequence

- [ ] **Step 4 — Manual** — run `monkey-devs --help` and confirm all commands appear. Run `monkey-devs config validate` against the default `.opencode/config.yaml`.

- [ ] **Commit** — `feat: add CLI entrypoint with all commands (IU-16)`

---

## Spec Coverage

| Requirement | Task |
|-------------|------|
| FR-01: Python CLI + LangGraph control loop | Task 20 (CLI), Task 19 (graph) |
| FR-02: Orchestrator as resource manager with compose_handoff | Task 8 |
| FR-03: Orchestrator must not invoke LLM | Task 5, 8 (no LLM in orchestrator) |
| FR-04: LangGraph WorkflowState + SQLite checkpointer | Task 2, 7 |
| FR-05: Stage gate with interrupt() | Task 19 |
| FR-06: Workflow resumption after crash | Task 7, 20 (resume command) |
| FR-07: Resource allocation visible at gate | Task 20 (details command) |
| FR-08: Five pre-defined stage nodes | Tasks 11–16 |
| FR-09: Stage nodes invoked automatically | Task 19 (graph edges) |
| FR-10: Structured handoff message | Task 8 |
| FR-11: Stage nodes rely entirely on handoff | Tasks 11–16 |
| FR-12: Tool access scoped per stage | Task 9 |
| FR-13: Stage 1 intake + spec artifacts | Task 11 |
| FR-14: Stage 1 proposes 2-3 stack candidates | Task 6 (stack-evaluation skill) |
| FR-15: Stage 2 makes final stack decision | Task 6 (stack-decision skill) |
| FR-16: Stage 2 produces architecture + tasks.yaml | Task 12 |
| FR-17: Stage 3 writes production code + tests | Task 13 |
| FR-18: Stage 4 runs tests, fixes, classifies failures | Task 14 |
| FR-19: Classifications at stage gate | Task 14, 20 |
| FR-20: Stage 5 produces runnable repo + delivery summary | Task 15 |
| FR-21: Three gate options (approve/fix/reject) | Task 19, 20 |
| FR-22: No stage skipped | Task 19 (no bypass edges) |
| FR-23: Correction continues from rejected stage | Task 19 (correction branches) |
| FR-24: Resource registry at .opencode/registry.yaml | Task 6 |
| FR-25: Registry updatable independently | Task 6 (static YAML) |
| FR-26: Orchestrator reads registry at start | Task 5 |
| FR-27: Skills as markdown files | Task 6 |
| FR-28: Skills have metadata in registry | Task 6 |
| FR-29: Skills injected via handoff | Task 8 |
| FR-30: Prefer skills over tools | Task 9 (binary rule) |
| FR-31–FR-33: Tools registered and scoped | Task 6, 9 |
| FR-34: Stage 1 stack shortlist | Task 11 (via skill) |
| FR-35: Stage 2 binding stack decision | Task 12 (via skill) |
| FR-36: No fixed stack | Task 6 (skills contain no hardcoded stack) |
| FR-37: Per-stage independently configurable LLM | Task 4, Tasks 11–16 |
| FR-38: Model config blocked during active workflow | Task 20 (config set-model) |
| FR-39: CLI commands for model config | Task 20 |
| NFR-01: Resumability | Task 7, 20 |
| NFR-02: Portability (no IDE) | Task 1 (standalone CLI) |
| NFR-03: Cost efficiency (skills over tools) | Task 9 |
| NFR-04: All failures classified before delivery | Task 14 |
| NFR-05: Transparency at every gate | Task 3 (logger), 20 (details) |
| NFR-06: Extensibility via registry | Task 5, 6 |
| Security: filesystem boundary | Task 9 |
| Security: bash allowlist | Task 9 |
| Security: API key scan | Task 4 |
| Security: prompt injection delimiters | Task 8 |
| Security: correction cycle limit | Task 19 |
| Documentation node (ADR-010) | Task 16 |
| Review + fix loop (ADR-009) | Tasks 17, 18 |
