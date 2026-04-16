"""Tool definitions available to monkey-devs agents."""

import asyncio
import json
import os
import pathlib
import shlex
import subprocess

class FilesystemBoundaryError(Exception):
    pass


class BashValidationError(Exception):
    pass


ALLOWLIST = {"pytest", "npm", "yarn", "cargo", "go", "make", "mvn", "python", "python3", "pip", "pip3"}

FILESYSTEM_READ = {
    "type": "function",
    "function": {
        "name": "filesystem_read",
        "description": "Read a file.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
}
FILESYSTEM_WRITE = {
    "type": "function",
    "function": {
        "name": "filesystem_write",
        "description": "Write a file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
}
FILESYSTEM_LIST = {
    "type": "function",
    "function": {
        "name": "filesystem_list",
        "description": "List a directory.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
}
BASH_EXECUTE = {
    "type": "function",
    "function": {
        "name": "bash_execute",
        "description": "Execute allowlisted shell command.",
        "parameters": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    },
}


def get_stage_tools(stage: int) -> list[dict]:
    base = [FILESYSTEM_READ, FILESYSTEM_WRITE, FILESYSTEM_LIST]
    return base + ([BASH_EXECUTE] if stage in (3, 4) else [])


def validate_path(path: str, project_root: str) -> str:
    root = pathlib.Path(os.path.realpath(project_root))
    resolved = pathlib.Path(os.path.realpath(os.path.join(project_root, path)))
    if not resolved.is_relative_to(root):
        raise FilesystemBoundaryError(f"Path {path!r} escapes project root")
    return str(resolved)


def validate_bash_command(command: str) -> None:
    try:
        tokens = shlex.split(command)
    except ValueError as e:
        raise BashValidationError(str(e))

    # Check metacharacters via substring search on raw command
    for meta in [";", "&&", "||", "$(", "`", "|", ">", "<"]:
        if meta in command:
            raise BashValidationError(f"Metacharacter {meta!r} in command")

    if not tokens:
        raise BashValidationError("Empty command")

    exe = tokens[0]
    if exe not in ALLOWLIST:
        raise BashValidationError(f"{exe!r} not on allowlist")

    if exe in ("pip", "pip3") and (len(tokens) < 2 or tokens[1] != "install"):
        raise BashValidationError("pip only permits 'install' subcommand")


async def execute_tool(tool_call: dict, stage: int, project_root: str = ".") -> str:
    name = tool_call["function"]["name"]
    args = json.loads(tool_call["function"]["arguments"])

    if name == "filesystem_read":
        p = validate_path(args["path"], project_root)
        return pathlib.Path(p).read_text()

    if name == "filesystem_write":
        p = validate_path(args["path"], project_root)
        pathlib.Path(p).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(p).write_text(args["content"])
        return "ok"

    if name == "filesystem_list":
        p = validate_path(args["path"], project_root)
        return "\n".join(str(x) for x in pathlib.Path(p).iterdir())

    if name == "bash_execute":
        validate_bash_command(args["command"])
        result = await asyncio.to_thread(
            subprocess.run,
            shlex.split(args["command"]),
            shell=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.stdout + result.stderr

    return f"Unknown tool: {name}"
