"""SQLite 连接与事务边界。

约定：
- 连接使用 autocommit（isolation_level=None），由 `transaction()` 显式开启写事务；
- 一个请求一个连接，连接存放在 Flask 的 g 上；
- 写操作使用 BEGIN IMMEDIATE，串行化"先检查名额、再写入"的临界区，
  避免并发报名突破人数上限。
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager

from flask import current_app, g

from .migrations import migrate


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        connection = sqlite3.connect(
            current_app.config["DATABASE"],
            isolation_level=None,  # 显式事务
            timeout=10,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        g.db = connection
    return g.db


def close_db(_exception: BaseException | None = None) -> None:
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


@contextmanager
def transaction():
    """显式写事务：成功提交，异常回滚。"""
    connection = get_db()
    if connection.in_transaction:  # 嵌套调用时复用外层事务
        yield connection
        return
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield connection
    except BaseException:
        connection.rollback()
        raise
    else:
        connection.commit()


def init_app(app) -> None:
    app.teardown_appcontext(close_db)
    with app.app_context():
        migrate(get_db())
