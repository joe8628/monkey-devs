# API Documentation

## Purpose
This skill governs how to produce `docs/api-reference.md` in Stage 5. It is a browsable reference for every public interface the project exposes — the document a developer opens when they want to know exactly what a function accepts, returns, and raises, without reading the source.

The source files (with docstrings added by `docstring-writing`) are the authoritative ground truth. This document organises and presents what is already there. It does not add information not in the source — it makes the source navigable.

## When to Apply
After `docstring-writing` has run and added Google-style docstrings to all public interfaces. If docstrings are absent or incomplete, the reference document will be incomplete — run `docstring-writing` first.

## Inputs

Read before writing:

- `docs/architecture.md` — the Interface Contracts section defines what the *intended* public API is. Use this to verify that the implemented API matches the design. If there is a discrepancy, note it in the document rather than silently documenting only one version.
- All source files in the main package (e.g., `monkey_devs/`) — these are the authoritative source of what is actually implemented. Read every file. Do not document from memory or from the architecture doc alone.
- `docs/delivery.md` — the Known Limitations section. Any interface that is incomplete or classified as a `code-issue` failure should be marked in the reference document.

Do not read test files for this skill — tests are not public API.

## Scope: What to Document

**Document:**
- Every public function and method (no leading underscore)
- Every public class and its public methods
- Every public constant or module-level value that callers may reference
- Every CLI command exposed via the entry point (if the project is a CLI)

**Do not document:**
- Private functions and methods (leading `_`)
- Internal implementation helpers not referenced in any Interface Contract
- Test utilities, fixtures, or conftest helpers
- Generated or auto-derived code

When in doubt, ask: "Could an external caller of this module need this?" If yes, document it. If it is only called by other functions within the same module, it is internal.

## Structure of `docs/api-reference.md`

Organise by module, not alphabetically by symbol. A developer navigates by "I am working with the config module" — not "I remember a function starts with L."

Within each module section:
1. Module-level description (one sentence — what the module is responsible for)
2. Classes (before standalone functions — classes are the primary interface in most modules)
3. Public functions and module-level constants

Within each class section:
1. Class description
2. `__init__` parameters (if non-trivial)
3. Public methods in the order a user would naturally call them (not alphabetical)

## Writing Each Entry

For every public function, method, or class, include:

**Name and module path**

Use the importable path:
```
monkey_devs.config.load_config
```

**Signature**

The exact function signature from source, including type annotations:
```python
def load_config(path: Path) -> AppConfig
```

**Purpose**

One sentence copied or lightly edited from the docstring summary line. Do not expand it — if the docstring is insufficient, that is a `docstring-writing` gap to fix, not a gap to paper over here.

**Parameters**

Each parameter: name, type, and what it must contain. Omit `self`. For parameters with default values, state the default and what it means:

```
path (Path): Absolute or relative path to config.yaml. Must exist and be readable.
```

**Returns**

Type and what the return value represents. If the function returns None or has a side effect only, say so:

```
Returns AppConfig: Validated configuration object with all provider settings populated.
```

**Raises**

Every exception the caller must handle — name the type and the condition that triggers it. Do not list exceptions that are only raised internally and always caught before returning:

```
ValueError: If the file is missing a required key or contains a literal API key.
FileNotFoundError: If path does not exist.
```

**Example**

One minimal working example. Use the project's actual import paths and realistic (but not sensitive) values. Do not use placeholder values like `"your-key-here"` — use `"sk-..."` or a descriptive string that clearly cannot be a real credential:

```python
from pathlib import Path
from monkey_devs.config import load_config

config = load_config(Path(".opencode/config.yaml"))
print(config.models.stage_1)
```

The example must compile and run correctly given the interface. Do not show examples that would fail.

## Discrepancies Between Design and Implementation

If the source implements a different signature than `docs/architecture.md`'s Interface Contracts specify, document both and note the discrepancy:

```
> **Note:** The architecture specifies `load_config(path: str)` but the implementation
> accepts `path: Path`. Callers should use `Path` objects.
```

Do not silently pick one or the other. The discrepancy is information a developer needs.

## Incomplete or Failed Interfaces

If `docs/delivery.md` lists a `code-issue` failure for a task that covers a specific interface, mark that interface in the reference:

```
> **Status:** Incomplete — classified as `code-issue` in Stage 4. Behaviour may not match the specification.
```

Do not omit the interface from the document. Document what exists and mark what is known to be wrong.

## Output Format

```markdown
# API Reference: [Project Name]

> Generated from source as of delivery. See [Delivery Summary](delivery.md) for known limitations.

## [module name] — `package.module`

[One sentence: what this module is responsible for.]

### `ClassName`

[One sentence class description.]

**Constructor parameters:**
- `param` (`Type`): description

#### `ClassName.method_name(param: Type) -> ReturnType`

[Purpose sentence.]

**Parameters:**
- `param` (`Type`): description

**Returns:** `ReturnType` — description

**Raises:**
- `ErrorType`: condition

**Example:**
```python
[minimal working example]
```

---

### `function_name(param: Type) -> ReturnType`

[Same structure as method entries above.]
```

Use `---` to separate top-level module sections for readability.

## Verification Before Finishing

1. Every entry has a source line in the actual code — nothing was documented from inference
2. Every example uses the correct import path (verify against the source)
3. Every interface listed in `docs/architecture.md`'s Interface Contracts appears in the reference
4. Any discrepancy between architecture and implementation is noted, not silently resolved

## Boundaries
- Do not document private functions — if it starts with `_`, skip it
- Do not add information not present in the source or docstrings — if a parameter's purpose is unclear, that is a `docstring-writing` gap
- Do not reorganise the source code to make it easier to document — document what exists
- Do not skip interfaces that have `code-issue` failures — mark them, do not omit them
- Do not duplicate the developer guide — this document answers "what does it accept and return," not "how does it work internally"
