"""数据库结构与版本迁移。

- v1：初始版本（两类报名、站内 + 出件箱通知）
- v2：change-v2（CR-01 年级限定报名、CR-02 MockEmailSender 邮件台账）

变更通过追加迁移步骤实现，不删库重建；迁移前后的行数由测试核对。
"""

from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 2

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


# v2：CR-01 报名方式增加 grade_limited；CR-02 新增邮件发送台账
ACTIVITIES_V2 = """
CREATE TABLE activities_v2 (
    activity_id TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    category    TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    start_at    TEXT NOT NULL,
    location    TEXT NOT NULL,
    capacity    INTEGER NOT NULL CHECK (capacity > 0),
    policy_type TEXT NOT NULL CHECK (policy_type IN ('direct', 'review', 'grade_limited')),
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
)
"""

EMAIL_DELIVERIES_V2 = """
CREATE TABLE IF NOT EXISTS email_deliveries (
    email_id     TEXT PRIMARY KEY,
    event_id     TEXT NOT NULL,
    student_id   TEXT NOT NULL,
    to_address   TEXT NOT NULL,
    subject      TEXT NOT NULL,
    body         TEXT NOT NULL,
    status       TEXT NOT NULL CHECK (status IN ('sent', 'failed')),
    error        TEXT,
    sent_at      TEXT NOT NULL,
    transport_id TEXT,
    UNIQUE (event_id, student_id)
)
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


def _upgrade_v1_to_v2(connection: sqlite3.Connection) -> None:
    """v1→v2：学生增加年级列、活动报名方式增加 grade_limited、新增邮件台账。"""
    connection.execute("PRAGMA foreign_keys = OFF")
    connection.execute("BEGIN")
    try:
        # CR-01：年级 1—4；既有演示账号按原有设定赋年级，其他学生默认大一
        connection.execute(
            "ALTER TABLE students ADD COLUMN grade INTEGER NOT NULL DEFAULT 1 "
            "CHECK (grade BETWEEN 1 AND 4)"
        )
        connection.execute(
            """
            UPDATE students
               SET grade = CASE student_id
                                WHEN 's1' THEN 2
                                WHEN 's2' THEN 3
                                WHEN 's3' THEN 1
                                WHEN 's4' THEN 4
                                WHEN 'admin' THEN 4
                                ELSE 1
                           END
            """
        )

        # CR-01：SQLite 无法直接修改 CHECK，重建 activities 表并复制数据
        connection.execute(ACTIVITIES_V2)
        connection.execute(
            """
            INSERT INTO activities_v2
                (activity_id, title, category, description, start_at, location,
                 capacity, policy_type, created_at, updated_at)
            SELECT activity_id, title, category, description, start_at, location,
                   capacity, policy_type, created_at, updated_at
              FROM activities
            """
        )
        connection.execute("DROP TABLE activities")
        connection.execute("ALTER TABLE activities_v2 RENAME TO activities")

        # CR-02：邮件发送台账（收件人 / 主题 / 内容 / 状态 / 时间 / 传输编号）
        connection.execute(EMAIL_DELIVERIES_V2)

        _set_version(connection, 2)
        connection.execute("COMMIT")
    except BaseException:
        connection.execute("ROLLBACK")
        raise
    finally:
        connection.execute("PRAGMA foreign_keys = ON")


def migrate(connection: sqlite3.Connection) -> int:
    """把数据库升级到当前代码所需的版本，返回最终版本号。"""
    version = _version(connection)
    if version < 1:
        connection.executescript(SCHEMA_V1)
        _set_version(connection, 1)
        version = 1
    if version < 2:
        _upgrade_v1_to_v2(connection)
        version = 2
    return version
