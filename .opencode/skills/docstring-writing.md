# Docstring Writing

## Purpose
This skill governs how to add Google-style docstrings to source files in Stage 5. Its output — inline documentation on every public interface — is the raw material that `api-documentation` reads to produce `docs/api-reference.md`. Write docstrings here once; the API reference presents them to the reader.

Docstrings are not decorations. They answer two questions the type signature alone cannot: what does the return value *mean*, and under what conditions does this raise? Every other detail — parameter names, types, return type — is already visible in the signature.

## When to Apply
After Stage 3 and 4 are complete and before `api-documentation` runs. Docstrings must exist in the source before the API reference is generated from them.

## Inputs

Read before editing anything:

- `docs/architecture.md` — the Interface Contracts section. Each public function listed there has a Purpose and Error specification. The docstring summary for that function must be consistent with this specification — not a paraphrase, not a rewrite.
- Each source module — read the full file before editing it. Never add a docstring without reading the function's implementation; a summary written from the signature alone is frequently wrong.

## Scope: What Gets a Docstring

**Always add if missing:**
- Every public function and method (no leading underscore)
- Every public class
- Every module (one-line module-level docstring at the top of the file)

**Add only if the logic is non-trivial:**
- Private functions and methods (leading `_`) — add when the function contains a non-obvious algorithm, a security constraint, or a known workaround that the next reader will not understand from the code alone

**Never add:**
- `__init__` methods that only assign parameters to `self` — the class docstring covers construction
- Test functions — test names are their documentation
- Stub functions that consist entirely of `pass` or `raise NotImplementedError`

**Never modify:**
- An existing docstring that is correct — even if you would have written it differently
- Implementation code while adding docstrings — this skill touches documentation only

## Process

### 1. Survey Each Module First

For each source file, read it completely and list:
- Which public functions lack docstrings
- Which classes lack docstrings
- Whether the module itself has a module-level docstring

Do this for all modules before editing any of them. A complete survey prevents the common failure of editing three files, then discovering the fourth has no docstrings and requires a different approach.

### 2. Write the Module Docstring

One sentence at the top of the file, before any imports. It names what the module is responsible for — drawn from `docs/architecture.md`'s Component section:

```python
"""Loads and validates .opencode/config.yaml into a typed AppConfig object."""
```

Do not describe the module's implementation or its dependencies. Name its responsibility.

### 3. Write Class Docstrings

One sentence naming what the class represents or manages. If the class is a data model, name what it models:

```python
class AppConfig(BaseModel):
    """Root configuration model for a monkey-devs workflow run."""
```

If construction requires non-obvious arguments or has preconditions the caller must satisfy, add an `Attributes:` section naming the key fields.

### 4. Write Function and Method Docstrings

Use this format:

```python
def function_name(param: Type) -> ReturnType:
    """One-sentence summary — what this function does, not how.

    Args:
        param: What this value represents and any constraint it must satisfy.

    Returns:
        What the returned value represents — not just its type.

    Raises:
        ErrorType: The condition that triggers this exception.
    """
```

**The summary line** — one sentence in the imperative form. Name the action and the subject:
- Good: `"Load and validate the config file at the given path."`
- Weak: `"This function loads the config."` — avoid "This function"
- Weak: `"Loads config."` — too brief to be useful; name what it loads and from where

Match the language of `docs/architecture.md`'s Interface Contract for this function. If the architecture says "raises ValueError with filename on parse error," the Raises section must say `ValueError` and name the condition.

**Args section** — include only when the parameter name and type together are insufficient:

| Include | Skip |
|---|---|
| `path: Path` — is this the project root or the config file? | `name: str` when the function is `set_name` |
| `stage: int` — valid range? 0–5 or 1–5? | `enabled: bool` on `set_enabled()` |
| A parameter with a non-obvious constraint | Any parameter whose purpose is self-evident from name + type |

Each arg description names what the value represents and any constraint it must satisfy. Do not restate the type — it is already in the signature.

**Returns section** — include whenever the return value's meaning is not obvious from the type alone:

| Include | Skip |
|---|---|
| `-> dict` — what keys does it contain? | `-> bool` on `is_valid()` |
| `-> str` — what does this string represent? | `-> AppConfig` on `load_config()` when the class name is self-explanatory |
| `-> list` — list of what? | `-> None` on a function with an obvious side effect |

Name what the value *means*, not what it *is*:
- Weak: `"Returns: str: The result."`
- Strong: `"Returns: Absolute path to the resolved file within the project root."`

**Raises section** — include only exceptions the *caller* must handle. Do not document internal exceptions that are always caught before the function returns:

| Include | Skip |
|---|---|
| `ValueError` from user-supplied invalid input | `KeyError` that is caught internally and re-raised as `ValueError` |
| `FileNotFoundError` from a path the caller provides | `TypeError` from a programming error (wrong argument type) that only a buggy caller would trigger |
| Any exception named in the Interface Contract | Internal implementation exceptions |

## Format Reference

```python
def load_config(path: Path) -> AppConfig:
    """Load and validate the config file at the given path.

    Args:
        path: Path to config.yaml, absolute or relative to the project root.

    Returns:
        Validated AppConfig with all provider and model settings populated.

    Raises:
        ValueError: If a required key is missing or a literal API key is detected.
        FileNotFoundError: If no file exists at path.
    """
```

## Verification Before Finishing

1. Every public function in every source module has a docstring
2. Every public class has a docstring
3. Every module has a module-level docstring
4. No existing correct docstring was modified
5. No implementation code was changed — only docstrings were added
6. Every Raises entry corresponds to an exception named in the Interface Contract or visibly raised in the function body

## Boundaries
- Do not add docstrings to test files — test names are their documentation
- Do not modify implementation code while adding docstrings
- Do not modify existing docstrings that are correct — even if style differs slightly
- Do not add an Args section that restates what the type annotation already says
- Do not document internal exceptions the function catches before returning
- Do not begin `api-documentation` until this skill has run on all source modules
