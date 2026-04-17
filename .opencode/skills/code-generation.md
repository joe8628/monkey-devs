# Code Generation

## Purpose
This skill governs the quality and style of production code written in Stage 3. It applies to Step 4 of the `tdd-implementation` cycle: the moment when a failing test exists and implementation begins. It does not govern process (that is `tdd-implementation`); it governs what good implementation code looks like.

## When to Apply
Every time you write or modify a production file in Stage 3. "Production file" means any file outside the `tests/` directory.

## Inputs
Two sources constrain what you write:

1. **The task's Interface section** — the function signatures, file paths, exception types, and data shapes the implementation must satisfy exactly. This is a contract, not a suggestion.
2. **The existing codebase** — the style, conventions, and patterns already established in adjacent files. Read them before writing.

## Step 1: Read the Codebase Before Writing

Before writing a single line, read the files most similar to what you are about to create:
- A new module in `monkey_devs/` → read 2–3 existing modules in `monkey_devs/`
- A new Pydantic model → read the existing models
- A new CLI command → read the existing CLI entry points

Look for:
- **Import order**: stdlib → third-party → local; alphabetical within groups?
- **Type annotations**: are public functions annotated? are internals annotated?
- **Docstring style**: does the project use one-line docstrings, multi-line, or none on private functions?
- **Exception types**: what custom exceptions exist? when are they raised vs. returning None?
- **Constant naming**: `ALL_CAPS` for module-level constants?
- **Class vs. function style**: dataclasses vs. Pydantic vs. plain classes?

Match what you observe. Do not introduce a new convention — if the project uses single-line docstrings on public functions, keep that. If it uses no docstrings on private functions, keep that.

## Step 2: Implement the Interface Contract Exactly

The Interface section of the task description defines the contract. Implement it exactly:

**Signatures must match** — parameter names, types, and order must be identical to what the Interface specifies. The tests were written against this contract; deviating breaks the tests.

**Return types must match** — if Interface says `-> AppConfig`, return an `AppConfig`, not a dict.

**Exceptions must match** — if Interface says `raises ValueError with filename on parse error`, raise `ValueError` (not `RuntimeError`, not a custom exception unless the Interface names one).

**Do not add parameters** — extra keyword arguments, `**kwargs`, or optional flags not in the Interface are scope creep. They will not be tested and will not be reviewed.

If the Interface is ambiguous on a detail (e.g., it says "raises an error" without naming the type), use the exception type already established in the codebase for similar situations. Do not invent a new one.

## Step 3: Error Handling Discipline

Handle errors only at **system boundaries** — points where the system interacts with something outside its control:

| Boundary | Example | Handle here |
|----------|---------|-------------|
| User input | CLI argument parsing, config file content | Yes |
| External API | LLM provider responses, HTTP calls | Yes |
| Filesystem | File reads/writes, path resolution | Yes |
| Internal calls | One module calling another | No |
| Known type operations | Pydantic model construction from valid input | No |

**Do not** wrap internal function calls in try/except unless the Interface explicitly requires it. Trust that your own code works. If a bug causes an unexpected exception, let it propagate so the error message identifies the actual source.

**Do not** add fallbacks or defaults that mask failures — if a required config key is missing, raise immediately with a message that names the key. Silent defaults hide real problems.

## Step 4: Write Self-Documenting Code

Name things so the code reads as a description of what it does:

- Functions: verb phrases that name the action — `load_config`, `validate_path`, `compose_handoff`
- Variables: noun phrases that name the content — `skill_paths`, `stage_tools`, `prior_artifacts`
- Booleans: predicates — `is_valid`, `has_checkpointer`, `path_exists`

**Add comments only where the logic is non-obvious** — meaning: a competent Python developer reading the code would stop and ask "why?". Examples that justify a comment:
- A non-intuitive algorithm choice
- A workaround for a known library limitation
- A security constraint that looks like an arbitrary restriction

**Do not add comments** explaining what the code does. `# Load the config file` above `config = load_config(path)` is noise, not documentation.

**Docstrings on public functions** — follow the project's existing style. If other public functions in the same module have docstrings, add one. If they don't, don't add one to introduce an inconsistency.

## Step 5: No Speculative Code

Implement only what the task requires:

- No helper functions that are not called by the task's code
- No configuration options not specified in the Interface
- No abstraction layers "for future flexibility"
- No feature flags, version guards, or backwards-compatibility shims
- No `__all__` unless the existing modules use it

Three similar lines of code in the task are better than a premature abstraction. The task-decomposition skill already decomposed the work into appropriate units — trust that decomposition.

## Step 6: Completeness Check Before Emitting

Before treating implementation as done, verify against the task:

1. **Every function in Interface exists** with the correct signature
2. **Every error case in Interface** raises the correct exception type
3. **No dead code** — every function you wrote is called by something
4. **No placeholder logic** — no `pass`, no `raise NotImplementedError`, no `return None` where a value is required
5. **The failing test from Step 3 of `tdd-implementation` would now pass** — trace through the logic mentally

If any check fails, fix the gap before emitting.

## Boundaries
- Do not change a function signature to avoid writing a harder implementation — implement the harder thing
- Do not catch exceptions and return None as a "safe default" unless the Interface explicitly specifies that behaviour
- Do not create new files beyond what the task requires — one task, one or two files
- Do not add logging or instrumentation unless it is specified in the task's Interface or How to verify section
