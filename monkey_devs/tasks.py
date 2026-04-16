"""Task definitions and task management for monkey-devs."""

import asyncio, os, pathlib, yaml


class TaskCycleError(Exception):
    pass


_lock = asyncio.Lock()


def load_tasks(path: pathlib.Path) -> list[dict]:
    return yaml.safe_load(path.read_text()).get("tasks", [])


def topological_sort(tasks: list[dict]) -> list[dict]:
    in_degree = {t["id"]: len(t.get("depends_on", [])) for t in tasks}
    queue = [t for t in tasks if in_degree[t["id"]] == 0]
    result = []
    while queue:
        node = queue.pop(0)
        result.append(node)
        for t in tasks:
            if node["id"] in t.get("depends_on", []):
                in_degree[t["id"]] -= 1
                if in_degree[t["id"]] == 0:
                    queue.append(t)
    if len(result) != len(tasks):
        raise TaskCycleError("Cycle detected in task depends_on")
    return result


def validate_tasks_yaml(path: pathlib.Path) -> None:
    data = yaml.safe_load(path.read_text())
    tasks = data.get("tasks", [])
    ids = {t["id"] for t in tasks}
    required = {"id", "title", "description", "status", "depends_on", "failure_classification"}
    valid_statuses = {"pending", "in-progress", "done"}
    for t in tasks:
        missing = required - set(t.keys())
        if missing:
            raise ValueError(f"Task {t.get('id')} missing fields: {missing}")
        if t["status"] not in valid_statuses:
            raise ValueError(f"Invalid status: {t['status']}")
        for dep in t.get("depends_on", []):
            if dep not in ids:
                raise ValueError(f"Unknown dependency: {dep}")


async def update_task_status(path: pathlib.Path, task_id: str, status: str) -> None:
    async with _lock:
        data = yaml.safe_load(path.read_text())
        for t in data["tasks"]:
            if t["id"] == task_id:
                t["status"] = status
        tmp = path.with_suffix(".yaml.tmp")
        tmp.write_text(yaml.dump(data, default_flow_style=False))
        os.replace(tmp, path)
