from langgraph.checkpoint.sqlite import SqliteSaver

from monkey_devs.graph import build_checkpointer


def test_checkpointer_creates_sqlite_file(tmp_path):
    db = tmp_path / "workflow-state.db"
    cp = build_checkpointer(db)
    assert db.exists()
    assert isinstance(cp, SqliteSaver)
