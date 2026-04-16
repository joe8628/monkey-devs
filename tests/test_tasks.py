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
