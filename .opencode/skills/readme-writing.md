# README Writing

## Purpose
This skill governs how to produce `README.md` in the project root during Stage 5. The README is the first document anyone reads when they encounter the repository — on GitHub, GitLab, or locally. It answers one question in under two minutes: "What is this, and can I run it?"

The README is a discovery document, not a reference manual. It links to deeper Stage 5 artifacts (`docs/developer-guide.md`, `docs/api-reference.md`) rather than duplicating them. Keep it short, accurate, and runnable.

## When to Apply
After `docs/delivery.md` has been written by `delivery-summary`. The delivery summary has already verified that all commands work and recorded the true test count. Use it as the source of truth — do not re-derive or re-verify commands that are already confirmed there.

## Inputs

Read before writing:

- `docs/delivery.md` — the authoritative source for setup commands, test commands, and project description. Copy commands from here verbatim; do not invent new ones.
- `docs/concept.md` — the original one-sentence problem statement and the Goals list. Use these to write the project description — they were written before any implementation bias.
- `docs/architecture.md` — the locked technology stack. Use this for the Prerequisites section (runtime version, key dependencies).
- `docs/spec.md` — the FR list. Use the first 3–5 FRs to write the Features section, translating requirement language into user-facing language.
- The project root directory — run a directory listing to build the Project Structure section from the actual tree, not from memory.

## Division of Labour with Other Stage 5 Skills

The README is shallow by design. If a reader needs more depth, link them there — do not expand the README to cover it.

| Content | Goes in README? | Goes where instead? |
|---|---|---|
| One-sentence project description | Yes | — |
| Prerequisites and install command | Yes | — |
| 2–3 usage examples with output | Yes | — |
| Full CLI command reference | No | `docs/api-reference.md` |
| Environment setup for contributors | No | `docs/developer-guide.md` |
| Module architecture and extension guide | No | `docs/developer-guide.md` |
| Known limitations and classified failures | No | `docs/delivery.md` |
| Full test output | No | `docs/delivery.md` |

If you find yourself writing a paragraph about internal architecture or a table of all CLI flags, stop — that belongs in a deeper document.

## Writing Each Section

### Project Name (H1)

The project name exactly as used in `pyproject.toml` or the equivalent package manifest. No tagline on the same line.

### One-Sentence Description

A single sentence that names what the project does and for whom. Pull from `docs/concept.md`'s problem statement — it was written before implementation bias set in.

**Weak** (names the implementation):
> A Python CLI using LangGraph and LiteLLM to run multi-agent workflows.

**Strong** (names the user value):
> Monkey Devs runs a five-stage AI-assisted development workflow that takes you from a project idea to a working, tested codebase without writing code manually.

### Prerequisites

List only what the user must have installed before running the install command. Do not list things the install command installs automatically.

Format:
```
- Python 3.11+
- [Any system-level dependency not installable via pip/uv]
```

If the only prerequisite is Python, say so. Do not list `uv`, `pip`, or `pytest` as prerequisites if they are installed as part of the setup.

### Installation

The exact install command from `docs/delivery.md`, in a code block. One command if possible. If configuration is required (env vars, config files), include the minimal required steps immediately after — do not send the user to another document for what they need to run the very first command.

```bash
[install command from docs/delivery.md]
```

If an env var or config file is required before first run, show a minimal working example:

```bash
export SOME_KEY=your-key-here
```

Do not say "see the developer guide for configuration options." Give them what they need to proceed.

### Usage

2–3 concrete examples. Each example must:
- Show the exact command
- Show the expected output or describe the observable result
- Represent a real use case, not a synthetic demo

Copy command patterns from `docs/delivery.md`. Do not invent examples that were not verified there.

```bash
$ monkey-devs run
[expected output]
```

Do not show every command or every flag. Show the golden path — the sequence a new user would actually run on first use.

### Running Tests

The exact test command from `docs/delivery.md`, in a code block, followed by the verified pass count:

```bash
uv run pytest
```

> NN tests pass as of delivery.

Do not describe what the tests cover. Do not list test files. One command, one outcome.

### Project Structure

A directory tree of the top-level structure, with one-line descriptions of each significant directory and file. Generate from the actual directory listing — do not reconstruct from memory.

Include:
- Source package directory
- Tests directory
- Configuration files (`pyproject.toml`, `.opencode/`)
- Key docs

Exclude:
- `__pycache__`, `.venv`, generated artifacts, lock files

```
project-root/
├── monkey_devs/     # main package
├── tests/           # test suite
├── docs/            # project documentation
├── .opencode/       # workflow registry, skills, and state
└── pyproject.toml   # package manifest and dependencies
```

Keep descriptions to a single line. This is orientation, not documentation.

### Links to Further Documentation

A brief list of the other Stage 5 documents for readers who want depth:

```markdown
## Further Documentation

- [API Reference](docs/api-reference.md) — public interface documentation
- [Developer Guide](docs/developer-guide.md) — setup, module structure, and extension
- [Delivery Summary](docs/delivery.md) — what was built, test results, and known limitations
```

Only link documents that actually exist. If `docs/api-reference.md` was not produced in this Stage 5 run, do not link it.

## Verification Before Finishing

Before writing the final file:

1. Every command in the README came from `docs/delivery.md` — verified there, not re-verified here
2. Every linked document in the Further Documentation section exists at the path stated
3. The project name matches `pyproject.toml`
4. The Prerequisites list contains only things not installed by the install command

## Output

Write to `README.md` in the project root. If a `README.md` already exists, read it first — preserve any sections not covered by this skill (e.g., a licence badge or contributor list) and update only the sections this skill defines.

## Boundaries
- Do not duplicate content from `docs/delivery.md` — link to it for Known Limitations and full test output
- Do not duplicate content from `docs/developer-guide.md` — link to it for architecture and extension
- Do not write commands you have not verified — use `docs/delivery.md` as the verified source
- Do not add marketing language, badges, or decorative elements unless the user requested them
- Do not link documents that do not exist
