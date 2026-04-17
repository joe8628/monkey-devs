"""JSONL structured run logger for Monkey Devs workflow events."""
import datetime
import json
import os
import pathlib
import uuid


class RunLogger:
    """Writes workflow events as JSONL. Rotates, keeping the 10 most recent log files."""

    def __init__(self, log_dir: pathlib.Path) -> None:
        log_dir = pathlib.Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%S")
        suffix = uuid.uuid4().hex[:8]
        self._path = log_dir / f"run-{ts}-{os.getpid()}-{suffix}.jsonl"
        self._path.touch()
        self._rotate(log_dir, keep=10)

    def log(self, event: str, **kwargs) -> None:
        """Append a structured event record to the current log file."""
        record = {"ts": datetime.datetime.now(datetime.UTC).isoformat(), "event": event, **kwargs}
        with self._path.open("a") as f:
            f.write(json.dumps(record) + "\n")

    @staticmethod
    def _rotate(log_dir: pathlib.Path, keep: int) -> None:
        logs = sorted(log_dir.glob("run-*.jsonl"))
        for old in logs[:-keep]:
            old.unlink(missing_ok=True)
