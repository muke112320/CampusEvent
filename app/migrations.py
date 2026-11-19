"""数据库结构与版本迁移。

基线版本 schema_version = 1。后续需求变更（change-v2）通过追加迁移步骤实现，
不允许直接删库重建，保证已有报名与通知数据可延续。
"""

from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 1

SCHEMA_V1 = """
CREATE TABLE IF NOT EXISTS students (
    student_id  TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT NOT NULL DEFAULT '',
    role        TEXT NOT NULL DEFAULT 'student'
                CHECK (role IN ('student', 'admin'))
);

CREATE TABLE IF NOT EXISTS activities (
    activity_id TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    category    TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    start_at    TEXT NOT NULL,
    location    TEXT NOT NULL,
    capacity    INTEGER NOT NULL CHECK (capacity > 0),
    policy_type TEXT NOT NULL CHECK (policy_type IN ('direct', 'review')),
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS registrations (
    registration_id TEXT PRIMARY KEY,
    activity_id     TEXT NOT NULL REFERENCES activities(activity_id) ON DELETE RESTRICT,
    student_id      TEXT NOT NULL REFERENCES students(student_id) ON DELETE RESTRICT,
    status          TEXT NOT NULL
                    CHECK (status IN ('pending', 'approved', 'rejected', 'cancelled')),
    note            TEXT NOT NULL DEFAULT '',
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

-- 同一学生对同一活动最多一条"待审核/已通过"的有效报名；
-- 已取消、已拒绝属于历史记录，不参与唯一性约束。
CREATE UNIQUE INDEX IF NOT EXISTS ux_registrations_active
    ON registrations(activity_id, student_id)
    WHERE status IN ('pending', 'approved');

CREATE TABLE IF NOT EXISTS messages (
    message_id  TEXT PRIMARY KEY,
    student_id  TEXT NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    activity_id TEXT REFERENCES activities(activity_id) ON DELETE SET NULL,
    category    TEXT NOT NULL,
    content     TEXT NOT NULL,
    is_read     INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS email_outbox (
    email_id     TEXT PRIMARY KEY,
    to_address   TEXT NOT NULL,
    subject      TEXT NOT NULL,
    body         TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    transport_id TEXT NOT NULL
);

-- 通知投递台账：既记录失败原因，也通过唯一约束实现事件级幂等。
CREATE TABLE IF NOT EXISTS notification_deliveries (
    delivery_id TEXT PRIMARY KEY,
    event_id    TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    subscriber  TEXT NOT NULL,
    channel     TEXT NOT NULL,
    student_id  TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'sent', 'failed')),
    error       TEXT,
    created_at  TEXT NOT NULL,
    UNIQUE (event_id, subscriber, student_id)
);
"""


def _version(connection: sqlite3.Connection) -> int:
    connection.execute(
        "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)"
    )
    row = connection.execute("SELECT version FROM schema_version").fetchone()
    if row is None:
        connection.execute("INSERT INTO schema_version (version) VALUES (0)")
        return 0
    return int(row[0])


def _set_version(connection: sqlite3.Connection, version: int) -> None:
    connection.execute("UPDATE schema_version SET version = ?", (version,))


def migrate(connection: sqlite3.Connection) -> int:
    """把数据库升级到当前代码所需的版本，返回最终版本号。"""
    version = _version(connection)
    if version < 1:
        connection.executescript(SCHEMA_V1)
        _set_version(connection, 1)
        version = 1
    return version
