"""LangGraph graph definition for monkey-devs workflow."""

import pathlib
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver


def build_checkpointer(db_path: pathlib.Path) -> SqliteSaver:
    """Create a SqliteSaver backed by db_path.

    The caller owns the connection lifetime. For a long-running CLI process
    this is safe — the OS reclaims the fd on exit. If you need explicit
    cleanup, call ``saver.conn.close()`` before shutdown.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    return SqliteSaver(conn)
