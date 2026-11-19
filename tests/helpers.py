"""测试辅助函数（数据库查询、账号切换）。"""

from __future__ import annotations

from app.db import get_db


def login(client, username: str = "s1"):
    """切换演示账号：先退出再登录，返回登录后的页面。"""
    client.post("/logout")
    response = client.post(
        "/login", data={"username": username}, follow_redirects=True
    )
    assert response.status_code == 200
    return response


def query_one(app, sql: str, params: tuple = ()):
    with app.app_context():
        return get_db().execute(sql, params).fetchone()


def query_all(app, sql: str, params: tuple = ()):
    with app.app_context():
        return get_db().execute(sql, params).fetchall()


def execute(app, sql: str, params: tuple = ()) -> None:
    with app.app_context():
        get_db().execute(sql, params)
