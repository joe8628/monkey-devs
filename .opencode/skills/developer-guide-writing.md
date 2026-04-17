# Developer Guide Writing

## Purpose
This skill governs how to produce `docs/developer-guide.md` in Stage 5. The developer guide is written for a Python developer who is new to this codebase but wants to extend or contribute to it — not for the end user running the workflow.

The README answers "how do I run this?" The API reference answers "what does this function accept?" The developer guide answers "how is this organised, how do I set up a dev environment, and how do I add something new?" These are different questions for a different reader. Do not duplicate the README or the API reference — link to them.

## When to Apply
After `docs/delivery.md`, `README.md`, and `docs/api-reference.md` have been written. The developer guide is the last substantial Stage 5 document. It draws on everything written before it and adds the contributor-level depth that the other documents deliberately omit.

## Inputs

Read before writing:

- `docs/architecture.md` — the System Design and Component sections define what each module is responsible for. Use these descriptions as the authoritative source for Module Descriptions, not your own inference from the source code.
- The source package directory (e.g., `monkey_devs/`) — read each module to verify the architecture description still matches the implementation. Note any drift.
- `.opencode/registry.yaml` — the actual registration format for skills and tools. The "Adding a New Skill" and "Adding a New Tool" sections must show the real schema, not a simplified one.
- `monkey_devs/tools.py` — the actual implementation pattern for tools (tool definition dict, `execute_tool` dispatch, `ALLOWLIST` for bash). The extension guide must match this pattern exactly.
- `docs/delivery.md` — the verified setup commands. Copy the dev environment setup from here rather than re-deriving it.
- `pyproject.toml` — package dependencies and dev dependencies, entry points, Python version constraint.

## Division of Labour with Other Stage 5 Skills

| Question | Developer Guide | API Reference | README |
|---|---|---|---|
| How is the project organised? | Yes | No | Brief tree only |
| What does each module own? | Yes | No | No |
| How do I set up a dev environment? | Yes | No | User setup only |
| What does function X accept? | No — link to API ref | Yes | No |
| How do I add a new skill? | Yes | No | No |
| How do I add a new tool? | Yes | No | No |
| Known limitations? | No — link to delivery.md | No | No |

## Writing Each Section

### 1. Project Structure

Generate a directory tree from the actual filesystem — do not reconstruct from memory. Include every top-level directory and the most important second-level items. Annotate each entry with one line describing what it contains and why it exists.

```
project-root/
├── monkey_devs/          # main package — orchestrator, config, graph, tools, tasks
│   ├── orchestrator.py   # compose_handoff() and skill/tool allocation
│   ├── config.py         # AppConfig Pydantic model and load_config()
│   ├── graph.py          # LangGraph graph definition and SqliteSaver factory
│   ├── tools.py          # tool definitions and execute_tool() dispatcher
│   └── tasks.py          # task YAML schema, loader, topological sort
├── tests/                # pytest test suite — mirrors monkey_devs/ structure
├── .opencode/
│   ├── registry.yaml     # skill and tool registry — the only file that needs updating to add capabilities
│   ├── skills/           # markdown skill files injected into stage handoffs
│   └── workflow-state.db # SQLite checkpoint (created at runtime)
└── pyproject.toml        # package manifest, dependencies, entry point
```

Keep annotations to a single line. This is a map, not documentation.

### 2. Module Descriptions

One subsection per module in the main package. For each:
- **Responsibility**: one sentence drawn from `docs/architecture.md`'s Component section — not paraphrased, not inferred from the code
- **Key functions/classes**: the 2–3 most important public symbols and what they do (one line each)
- **What it does not do**: one sentence of explicit non-responsibility, matching the architecture doc

This section is not the API reference — do not list every function. Point the reader to `docs/api-reference.md` for the full interface.

Example format:

```markdown
#### `monkey_devs/config.py`

**Responsibility**: Loads and validates `.opencode/config.yaml` into a typed `AppConfig` object.

**Key symbols**:
- `load_config(path: Path) -> AppConfig` — parses YAML and validates against the Pydantic schema
- `AppConfig` — root Pydantic model; `models`, `providers`, `timeouts` sub-models

**Does not**: write config files, set defaults for missing providers, or interact with the filesystem beyond reading the specified path.

See [API Reference](api-reference.md) for full signatures.
```

### 3. Environment Setup

Steps to create a working development environment from a clean checkout. Distinct from the README's user install — this includes dev dependencies, test tooling, and any local configuration needed to run the test suite.

Copy the base install command from `docs/delivery.md`. Add dev-specific steps:

```bash
# 1. Install with dev dependencies
uv sync --dev

# 2. Verify the install
uv run pytest
```

If any environment variables or config files must exist before the tests run, show exactly how to create them — a minimal working `.opencode/config.yaml` with dummy values is better than "configure your API keys."

All commands must work exactly as written. Do not describe a setup you have not verified.

### 4. Running Tests

The test command, how to run a subset, and how to read the output:

```bash
# Full suite
uv run pytest

# Single module
uv run pytest tests/test_config.py

# Single test with verbose output
uv run pytest tests/test_config.py::test_load_valid_config -xvs
```

State what a passing run looks like (test count from `docs/delivery.md`). State what a failure looks like and how to read the pytest output — specifically: where to find the assertion that failed and where to find the stack trace.

Do not describe the test categories or what each test file covers — that belongs in the test files themselves.

### 5. Adding a New Skill

This is the most important extension path for Monkey Devs. A skill is a markdown prompt file that gets injected into a stage agent's handoff message. Adding one requires two steps and only two steps.

**Step 1: Write the skill file**

Create `.opencode/skills/<skill-name>.md`. The file must have:
- A `# Title` heading
- A `## Purpose` section explaining what behaviour the skill governs and when it applies
- The body: process steps, quality criteria, output format, and boundaries

Follow the same structure used by the existing skills in `.opencode/skills/`. No frontmatter is required.

**Step 2: Register in `registry.yaml`**

Add an entry under the `skills:` key in `.opencode/registry.yaml`:

```yaml
skills:
  - name: my-skill-name
    description: "One sentence: what this skill does and when it triggers"
    stages: [3]          # list of stage numbers where this skill is injected
    path: .opencode/skills/my-skill-name.md
```

Field rules:
- `name`: lowercase, hyphenated, unique across all entries
- `description`: used by the orchestrator's resource allocation display — be specific
- `stages`: the integers 1–5; stage 0 is reserved for orchestrator-internal skills
- `path`: relative to the project root; the file must exist at this path

No code changes are required. The orchestrator reads the registry at workflow start and injects skills into handoffs automatically via `compose_handoff()`.

**Verify**: Start a workflow run and check the stage gate output — the new skill name should appear in the resource allocation summary for the stages you specified.

### 6. Adding a New Tool

A tool is an executable capability — something a stage agent can invoke at runtime. Adding one requires three steps.

**Step 1: Define the tool schema in `tools.py`**

Add a tool definition dict following the OpenAI function-calling schema. Follow the exact pattern of the existing definitions in `monkey_devs/tools.py`:

```python
MY_TOOL = {
    "type": "function",
    "function": {
        "name": "my_tool_name",
        "description": "What this tool does — shown to the agent deciding whether to call it.",
        "parameters": {
            "type": "object",
            "properties": {
                "param_name": {"type": "string", "description": "What this parameter is"},
            },
            "required": ["param_name"],
        },
    },
}
```

**Step 2: Handle the tool call in `execute_tool()`**

Add a branch to the `execute_tool()` dispatcher in `monkey_devs/tools.py`:

```python
elif name == "my_tool_name":
    # validate inputs
    # perform the operation
    return result_string
```

Security constraints:
- If the tool touches the filesystem, call `validate_path()` before any read or write — this enforces the project root boundary
- If the tool runs a shell command, call `validate_bash_command()` first and pass a `shlex.split()` list to `subprocess.run()` with `shell=False`
- Return a string — the agent receives tool output as text

**Step 3: Register in `registry.yaml`**

Add an entry under the `tools:` key:

```yaml
tools:
  - name: my-tool-name
    description: "What this tool does — used in stage gate display"
    type: builtin          # builtin | mcp
    stages: [3, 4]         # stages where agents can call this tool
    connection: builtin    # builtin | optional | <connection-string>
```

The `stages` list controls which stage agents receive this tool in their handoff. An agent cannot call a tool not listed for its stage — `get_tools_for_stage()` enforces this.

**Verify**: Write a test in `tests/test_tools.py` that calls `execute_tool()` with a tool call dict for your new tool and asserts the correct return value. Run `uv run pytest tests/test_tools.py -xvs`.

## Verification Before Finishing

1. Every command in the document runs correctly from the project root
2. The registry.yaml schema shown in sections 5 and 6 matches the actual current schema in `.opencode/registry.yaml`
3. The `tools.py` patterns shown in section 6 match the actual current patterns in `monkey_devs/tools.py`
4. Every module in the main package has an entry in section 2
5. All cross-references (`docs/api-reference.md`, `docs/delivery.md`) point to files that exist

## Output

Write to `docs/developer-guide.md`. If the file already exists, read it first and update only the sections this skill defines.

## Boundaries
- Do not duplicate the API reference — describe what modules own, link to api-reference.md for signatures
- Do not duplicate the README — link to it for user-facing setup; the dev environment section here is for contributors
- Do not describe the tool registration pattern from memory — read `tools.py` and `registry.yaml` and show the actual current pattern
- Do not include deployment, packaging, or publishing steps — those are out of scope per the project's Non-Goals
