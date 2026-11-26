"""数据访问层：把 SQL 细节与领域/服务层隔离。

仓储只做"对象 <-> 行"的转换与简单查询，不含业务判断；
业务规则放在 services/ 与 domain/ 中。
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from .domain.models import (
    Activity,
    Message,
    PolicyType,
    Registration,
    RegistrationStats,
    RegistrationStatus,
    Role,
    Student,
)
from .domain.models import new_id


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def _escape_like(keyword: str) -> str:
    return keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@dataclass(frozen=True)
class RegistrationDetail:
    """报名 + 活动 + 学生的读模型，供列表/审批页面一次查询取得。"""

    registration: Registration
    activity: Activity
    student: Student


_ACTIVITY_COLUMNS = (
    "a.activity_id, a.title, a.category, a.description, a.start_at, a.location, "
    "a.capacity, a.policy_type, a.created_at AS act_created_at, a.updated_at AS act_updated_at"
)


class ActivityRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    @staticmethod
    def _to_activity(row: sqlite3.Row) -> Activity:
        return Activity(
            activity_id=row["activity_id"],
            title=row["title"],
            category=row["category"],
            description=row["description"],
            start_at=_dt(row["start_at"]),
            location=row["location"],
            capacity=row["capacity"],
            policy_type=PolicyType(row["policy_type"]),
            created_at=_dt(row["act_created_at"]),
            updated_at=_dt(row["act_updated_at"]),
        )

    def add(self, activity: Activity) -> None:
        self.connection.execute(
            """
            INSERT INTO activities (activity_id, title, category, description, start_at,
                                    location, capacity, policy_type, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                activity.activity_id,
                activity.title,
                activity.category,
                activity.description,
                _iso(activity.start_at),
                activity.location,
                activity.capacity,
                activity.policy_type.value,
                _iso(activity.created_at),
                _iso(activity.updated_at),
            ),
        )

    def update(self, activity: Activity) -> None:
        self.connection.execute(
            """
            UPDATE activities
               SET title = ?, category = ?, description = ?, start_at = ?, location = ?,
                   capacity = ?, policy_type = ?, updated_at = ?
             WHERE activity_id = ?
            """,
            (
                activity.title,
                activity.category,
                activity.description,
                _iso(activity.start_at),
                activity.location,
                activity.capacity,
                activity.policy_type.value,
                _iso(activity.updated_at),
                activity.activity_id,
            ),
        )

    def get(self, activity_id: str) -> Activity | None:
        row = self.connection.execute(
            f"SELECT {_ACTIVITY_COLUMNS} FROM activities a WHERE a.activity_id = ?",
            (activity_id,),
        ).fetchone()
        return self._to_activity(row) if row else None

    def list(self, keyword: str = "") -> list[Activity]:
        if keyword:
            pattern = f"%{_escape_like(keyword)}%"
            rows = self.connection.execute(
                f"""SELECT {_ACTIVITY_COLUMNS} FROM activities a
                    WHERE a.title LIKE ? ESCAPE '\\'
                    ORDER BY a.start_at ASC""",
                (pattern,),
            ).fetchall()
        else:
            rows = self.connection.execute(
                f"SELECT {_ACTIVITY_COLUMNS} FROM activities a ORDER BY a.start_at ASC"
            ).fetchall()
        return [self._to_activity(row) for row in rows]

    def delete(self, activity_id: str) -> None:
        self.connection.execute("DELETE FROM activities WHERE activity_id = ?", (activity_id,))

    def count_registrations(self, activity_id: str) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) AS n FROM registrations WHERE activity_id = ?", (activity_id,)
        ).fetchone()
        return int(row["n"])


class StudentRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    @staticmethod
    def _to_student(row: sqlite3.Row) -> Student:
        return Student(
            student_id=row["student_id"],
            name=row["name"],
            email=row["email"],
            role=Role(row["role"]),
            grade=int(row["grade"]),
        )

    def add(self, student: Student) -> None:
        self.connection.execute(
            "INSERT INTO students (student_id, name, email, role, grade) VALUES (?, ?, ?, ?, ?)",
            (student.student_id, student.name, student.email, student.role.value, student.grade),
        )

    def get(self, student_id: str) -> Student | None:
        row = self.connection.execute(
            "SELECT * FROM students WHERE student_id = ?", (student_id,)
        ).fetchone()
        return self._to_student(row) if row else None

    def list_all(self) -> list[Student]:
        rows = self.connection.execute(
            "SELECT * FROM students ORDER BY role DESC, student_id ASC"
        ).fetchall()
        return [self._to_student(row) for row in rows]

    def count(self) -> int:
        return int(self.connection.execute("SELECT COUNT(*) AS n FROM students").fetchone()["n"])


class RegistrationRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    @staticmethod
    def _to_registration(row: sqlite3.Row) -> Registration:
        return Registration(
            registration_id=row["registration_id"],
            activity_id=row["activity_id"],
            student_id=row["student_id"],
            status=RegistrationStatus(row["status"]),
            note=row["note"],
            created_at=_dt(row["created_at"]),
            updated_at=_dt(row["updated_at"]),
        )

    @staticmethod
    def _to_detail(row: sqlite3.Row) -> RegistrationDetail:
        activity = Activity(
            activity_id=row["activity_id"],
            title=row["title"],
            category=row["category"],
            description=row["description"],
            start_at=_dt(row["start_at"]),
            location=row["location"],
            capacity=row["capacity"],
            policy_type=PolicyType(row["policy_type"]),
            created_at=_dt(row["act_created_at"]),
            updated_at=_dt(row["act_updated_at"]),
        )
        student = Student(
            student_id=row["student_id"],
            name=row["student_name"],
            email=row["student_email"],
            role=Role(row["student_role"]),
            grade=int(row["student_grade"]),
        )
        registration = Registration(
            registration_id=row["registration_id"],
            activity_id=row["activity_id"],
            student_id=row["student_id"],
            status=RegistrationStatus(row["reg_status"]),
            note=row["note"],
            created_at=_dt(row["reg_created_at"]),
            updated_at=_dt(row["reg_updated_at"]),
        )
        return RegistrationDetail(registration=registration, activity=activity, student=student)

    _DETAIL_SELECT = f"""
        SELECT r.registration_id, r.activity_id, r.student_id,
               r.status AS reg_status, r.note,
               r.created_at AS reg_created_at, r.updated_at AS reg_updated_at,
               {_ACTIVITY_COLUMNS},
               s.name AS student_name, s.email AS student_email, s.role AS student_role,
               s.grade AS student_grade
          FROM registrations r
          JOIN activities a ON a.activity_id = r.activity_id
          JOIN students s ON s.student_id = r.student_id
    """

    def add(self, registration: Registration) -> None:
        self.connection.execute(
            """
            INSERT INTO registrations (registration_id, activity_id, student_id, status,
                                       note, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                registration.registration_id,
                registration.activity_id,
                registration.student_id,
                registration.status.value,
                registration.note,
                _iso(registration.created_at),
                _iso(registration.updated_at),
            ),
        )

    def update_status(self, registration: Registration) -> None:
        self.connection.execute(
            "UPDATE registrations SET status = ?, note = ?, updated_at = ? WHERE registration_id = ?",
            (
                registration.status.value,
                registration.note,
                _iso(registration.updated_at),
                registration.registration_id,
            ),
        )

    def get(self, registration_id: str) -> Registration | None:
        row = self.connection.execute(
            "SELECT * FROM registrations WHERE registration_id = ?", (registration_id,)
        ).fetchone()
        return self._to_registration(row) if row else None

    def get_detail(self, registration_id: str) -> RegistrationDetail | None:
        row = self.connection.execute(
            self._DETAIL_SELECT + " WHERE r.registration_id = ?", (registration_id,)
        ).fetchone()
        return self._to_detail(row) if row else None

    def find_active(self, activity_id: str, student_id: str) -> Registration | None:
        row = self.connection.execute(
            """
            SELECT * FROM registrations
             WHERE activity_id = ? AND student_id = ?
               AND status IN ('pending', 'approved')
             LIMIT 1
            """,
            (activity_id, student_id),
        ).fetchone()
        return self._to_registration(row) if row else None

    def find_latest(self, activity_id: str, student_id: str) -> Registration | None:
        """取最近一条报名（含历史状态），用于在详情页展示取消/拒绝结果。"""
        row = self.connection.execute(
            """
            SELECT * FROM registrations
             WHERE activity_id = ? AND student_id = ?
             ORDER BY created_at DESC
             LIMIT 1
            """,
            (activity_id, student_id),
        ).fetchone()
        return self._to_registration(row) if row else None

    def list_for_student(self, student_id: str) -> list[RegistrationDetail]:
        rows = self.connection.execute(
            self._DETAIL_SELECT + " WHERE r.student_id = ? ORDER BY r.created_at DESC",
            (student_id,),
        ).fetchall()
        return [self._to_detail(row) for row in rows]

    def list_for_activity(
        self, activity_id: str, statuses: tuple[RegistrationStatus, ...] | None = None
    ) -> list[RegistrationDetail]:
        query = self._DETAIL_SELECT + " WHERE r.activity_id = ?"
        params: list[object] = [activity_id]
        if statuses:
            placeholders = ", ".join("?" for _ in statuses)
            query += f" AND r.status IN ({placeholders})"
            params.extend(status.value for status in statuses)
        query += " ORDER BY r.created_at ASC"
        rows = self.connection.execute(query, params).fetchall()
        return [self._to_detail(row) for row in rows]

    def list_pending(self, activity_id: str | None = None) -> list[RegistrationDetail]:
        query = self._DETAIL_SELECT + " WHERE r.status = 'pending'"
        params: list[object] = []
        if activity_id:
            query += " AND r.activity_id = ?"
            params.append(activity_id)
        query += " ORDER BY r.created_at ASC"
        rows = self.connection.execute(query, params).fetchall()
        return [self._to_detail(row) for row in rows]

    def count_by_status(self, activity_id: str, status: RegistrationStatus) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) AS n FROM registrations WHERE activity_id = ? AND status = ?",
            (activity_id, status.value),
        ).fetchone()
        return int(row["n"])

    def stats(self, activity_id: str, capacity: int) -> RegistrationStats:
        return RegistrationStats(
            activity_id=activity_id,
            capacity=capacity,
            approved=self.count_by_status(activity_id, RegistrationStatus.APPROVED),
            pending=self.count_by_status(activity_id, RegistrationStatus.PENDING),
        )


class MessageRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    @staticmethod
    def _to_message(row: sqlite3.Row) -> Message:
        return Message(
            message_id=row["message_id"],
            student_id=row["student_id"],
            activity_id=row["activity_id"],
            category=row["category"],
            content=row["content"],
            is_read=bool(row["is_read"]),
            created_at=_dt(row["created_at"]),
        )

    def add(self, message: Message) -> None:
        self.connection.execute(
            """
            INSERT INTO messages (message_id, student_id, activity_id, category,
                                  content, is_read, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message.message_id,
                message.student_id,
                message.activity_id,
                message.category,
                message.content,
                int(message.is_read),
                _iso(message.created_at),
            ),
        )

    def list_for_student(self, student_id: str, limit: int = 100) -> list[Message]:
        rows = self.connection.execute(
            "SELECT * FROM messages WHERE student_id = ? ORDER BY created_at DESC LIMIT ?",
            (student_id, limit),
        ).fetchall()
        return [self._to_message(row) for row in rows]

    def unread_count(self, student_id: str) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) AS n FROM messages WHERE student_id = ? AND is_read = 0",
            (student_id,),
        ).fetchone()
        return int(row["n"])

    def mark_all_read(self, student_id: str) -> None:
        self.connection.execute(
            "UPDATE messages SET is_read = 1 WHERE student_id = ? AND is_read = 0",
            (student_id,),
        )


class EmailOutboxRepository:
    """模拟邮件网关的出件箱：真实系统会替换为 SMTP/邮件服务。"""

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def add(self, to_address: str, subject: str, body: str, transport_id: str) -> str:
        email_id = new_id("MAIL")
        self.connection.execute(
            """
            INSERT INTO email_outbox (email_id, to_address, subject, body, created_at, transport_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (email_id, to_address, subject, body, _iso(datetime.now()), transport_id),
        )
        return email_id

    def list_recent(self, limit: int = 20) -> list[sqlite3.Row]:
        return self.connection.execute(
            "SELECT * FROM email_outbox ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()


class EmailDeliveryRepository:
    """邮件发送台账（change-v2 / CR-02）。

    每封模拟邮件记录收件人、主题、内容、状态与时间；同一事件对同一学生
    只允许一条记录，从数据层保证"同一业务事件不重复发送"。
    """

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def record(
        self,
        *,
        email_id: str,
        event_id: str,
        student_id: str,
        to_address: str,
        subject: str,
        body: str,
        status: str,
        error: str | None,
        sent_at: datetime,
        transport_id: str | None,
    ) -> bool:
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO email_deliveries
                (email_id, event_id, student_id, to_address, subject, body,
                 status, error, sent_at, transport_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                email_id,
                event_id,
                student_id,
                to_address,
                subject,
                body,
                status,
                error,
                _iso(sent_at),
                transport_id,
            ),
        )
        return cursor.rowcount == 1

    def find_for_event(self, event_id: str, student_id: str) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT * FROM email_deliveries WHERE event_id = ? AND student_id = ?",
            (event_id, student_id),
        ).fetchone()

    def list_recent(self, limit: int = 20) -> list[sqlite3.Row]:
        return self.connection.execute(
            "SELECT * FROM email_deliveries ORDER BY sent_at DESC LIMIT ?", (limit,)
        ).fetchall()

    def count_by_status(self, status: str) -> int:
        return int(
            self.connection.execute(
                "SELECT COUNT(*) AS n FROM email_deliveries WHERE status = ?", (status,)
            ).fetchone()["n"]
        )


class NotificationDeliveryRepository:
    """通知投递台账：claim 保证幂等，mark 记录成功/失败。"""

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def claim(self, event_id: str, event_type: str, subscriber: str, channel: str, student_id: str) -> str | None:
        delivery_id = f"DLV-{uuid4().hex[:12].upper()}"
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO notification_deliveries
                (delivery_id, event_id, event_type, subscriber, channel, student_id, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (delivery_id, event_id, event_type, subscriber, channel, student_id, _iso(datetime.now())),
        )
        return delivery_id if cursor.rowcount == 1 else None

    def mark(self, delivery_id: str, status: str, error: str | None = None) -> None:
        self.connection.execute(
            "UPDATE notification_deliveries SET status = ?, error = ? WHERE delivery_id = ?",
            (status, error, delivery_id),
        )

    def list_recent(self, limit: int = 80) -> list[sqlite3.Row]:
        return self.connection.execute(
            "SELECT * FROM notification_deliveries ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()

    def count_failed(self) -> int:
        return int(
            self.connection.execute(
                "SELECT COUNT(*) AS n FROM notification_deliveries WHERE status = 'failed'"
            ).fetchone()["n"]
        )
