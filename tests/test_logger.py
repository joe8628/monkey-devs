import json
import os
from monkey_devs.logger import RunLogger


def test_log_event_writes_jsonl(tmp_path):
    logger = RunLogger(log_dir=tmp_path)
    logger.log("workflow_started", project="test-proj")
    log_files = list(tmp_path.iterdir())
    assert len(log_files) == 1
    lines = log_files[0].read_text().splitlines()
    event = json.loads(lines[0])
    assert event["event"] == "workflow_started"
    assert event["project"] == "test-proj"
    assert "ts" in event


def test_log_rotation_keeps_10_files(tmp_path):
    # Create 11 loggers — should keep only 10 files
    for _ in range(11):
        RunLogger(log_dir=tmp_path)
    assert len(list(tmp_path.glob("run-*.jsonl"))) == 10


def test_multiple_events_append_to_same_file(tmp_path):
    logger = RunLogger(log_dir=tmp_path)
    logger.log("stage_started", stage=1)
    logger.log("stage_completed", stage=1)
    lines = list(tmp_path.iterdir())[0].read_text().splitlines()
    assert len(lines) == 2


def test_log_filename_includes_process_id(tmp_path):
    logger = RunLogger(log_dir=tmp_path)
    assert f"-{os.getpid()}-" in logger._path.name
