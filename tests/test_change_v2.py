"""change-v2 教师变更单测试：CR-01 年级限定报名 + CR-02 MockEmailSender 邮件通知。

对应教师材料中的 CR1-01—CR1-05、CR2-01—CR2-05。
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta

import pytest

from app import create_app
from app.dependencies import get_container
from app.domain.events import RegistrationApproved
from app.migrations import SCHEMA_V1, migrate
from tests.helpers import login, query_all, query_one


def _future(days: int = 5) -> str:
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M")


# ---------------------------------------------------------------------------
# CR-01 年级限定报名
# ---------------------------------------------------------------------------
def test_cr1_01_grade2_student_can_register(client, app, make_activity):
    """CR1-01：大二学生报名年级限定活动 → 通过。"""
    activity = make_activity(title="CR1 大二活动", capacity=5, policy="grade_limited")
    login(client, "s1")  # s1 = 大二
    response = client.post(
        f"/activities/{activity.activity_id}/register", follow_redirects=True
    )
    assert "报名成功" in response.get_data(as_text=True)
    row = query_one(
        app,
        "SELECT status FROM registrations WHERE activity_id = ? AND student_id = 's1'",
        (activity.activity_id,),
    )
    assert row["status"] == "approved"


def test_cr1_02_grade3_student_can_register(client, app, make_activity):
    """CR1-02：大三学生报名年级限定活动 → 通过。"""
    activity = make_activity(title="CR1 大三活动", capacity=5, policy="grade_limited")
    login(client, "s2")  # s2 = 大三
    response = client.post(
        f"/activities/{activity.activity_id}/register", follow_redirects=True
    )
    assert "报名成功" in response.get_data(as_text=True)
    row = query_one(
        app,
        "SELECT status FROM registrations WHERE activity_id = ? AND student_id = 's2'",
        (activity.activity_id,),
    )
    assert row["status"] == "approved"


def test_cr1_03_grade1_student_rejected_with_reason(client, app, make_activity):
    """CR1-03：大一学生报名年级限定活动 → 拒绝并显示原因。"""
    activity = make_activity(title="CR1 大一拦截", capacity=5, policy="grade_limited")
    login(client, "s3")  # s3 = 大一
    response = client.post(
        f"/activities/{activity.activity_id}/register", follow_redirects=True
    )
    html = response.get_data(as_text=True)
    assert "仅限大二、大三" in html
    assert "大一" in html
    assert query_one(
        app,
        "SELECT COUNT(*) AS n FROM registrations WHERE activity_id = ?",
        (activity.activity_id,),
    )["n"] == 0


def test_cr1_04_grade4_student_rejected_with_reason(client, app, make_activity):
    """CR1-04：大四学生报名年级限定活动 → 拒绝并显示原因。"""
    activity = make_activity(title="CR1 大四拦截", capacity=5, policy="grade_limited")
    login(client, "s4")  # s4 = 大四
    response = client.post(
        f"/activities/{activity.activity_id}/register", follow_redirects=True
    )
    html = response.get_data(as_text=True)
    assert "仅限大二、大三" in html
    assert "大四" in html
    assert query_one(
        app,
        "SELECT COUNT(*) AS n FROM registrations WHERE activity_id = ?",
        (activity.activity_id,),
    )["n"] == 0


def test_cr1_capacity_limit_still_applies(client, app, make_activity):
    """年级符合也必须遵守名额限制：容量 1 时第二位大二学生失败。"""
    activity = make_activity(title="CR1 名额限制", capacity=1, policy="grade_limited")
    login(client, "s1")
    client.post(f"/activities/{activity.activity_id}/register", follow_redirects=True)
    login(client, "s2")
    response = client.post(
        f"/activities/{activity.activity_id}/register", follow_redirects=True
    )
    assert "名额已满" in response.get_data(as_text=True)
    approved = query_one(
        app,
        "SELECT COUNT(*) AS n FROM registrations WHERE activity_id = ? AND status = 'approved'",
        (activity.activity_id,),
    )
    assert approved["n"] == 1


def test_cr1_duplicate_registration_still_rejected(client, app, make_activity):
    """年级符合也必须遵守重复报名限制。"""
    activity = make_activity(title="CR1 重复报名", capacity=5, policy="grade_limited")
    login(client, "s1")
    client.post(f"/activities/{activity.activity_id}/register", follow_redirects=True)
    response = client.post(
        f"/activities/{activity.activity_id}/register", follow_redirects=True
    )
    assert "不能重复报名" in response.get_data(as_text=True)
    rows = query_all(
        app,
        "SELECT * FROM registrations WHERE activity_id = ? AND student_id = 's1'",
        (activity.activity_id,),
    )
    assert len(rows) == 1


def test_cr1_existing_policies_unchanged(client, app, make_activity):
    """CR1-05 的一部分：原有直接报名/审核报名行为不变（大一也能直接报名）。"""
    direct = make_activity(title="CR1 原直接报名", capacity=2, policy="direct")
    login(client, "s3")  # 大一
    response = client.post(
        f"/activities/{direct.activity_id}/register", follow_redirects=True
    )
    assert "报名成功" in response.get_data(as_text=True)

    review = make_activity(title="CR1 原审核报名", capacity=2, policy="review")
    login(client, "s3")
    response = client.post(
        f"/activities/{review.activity_id}/register", follow_redirects=True
    )
    assert "待审核" in response.get_data(as_text=True)
    row = query_one(
        app,
        "SELECT status FROM registrations WHERE activity_id = ? AND student_id = 's3'",
        (review.activity_id,),
    )
    assert row["status"] == "pending"


# ---------------------------------------------------------------------------
# CR-02 模拟邮件通知
# ---------------------------------------------------------------------------
def test_cr2_01_direct_approval_records_message_and_email(client, app, make_activity):
    """CR2-01：直接报名通过 → 站内消息与模拟邮件均有记录。"""
    activity = make_activity(title="CR2 直接报名", capacity=3)
    login(client, "s1")
    client.post(f"/activities/{activity.activity_id}/register", follow_redirects=True)

    messages = query_all(
        app,
        "SELECT * FROM messages WHERE student_id = 's1' AND activity_id = ?",
        (activity.activity_id,),
    )
    assert len(messages) == 1
    assert "报名成功" in messages[0]["content"]

    emails = query_all(app, "SELECT * FROM email_deliveries WHERE student_id = 's1'")
    assert len(emails) == 1
    assert emails[0]["status"] == "sent"
    assert emails[0]["to_address"] == "zhangxiaoming@campus.edu.cn"
    assert emails[0]["subject"]
    assert emails[0]["body"]
    assert emails[0]["sent_at"]
    assert emails[0]["transport_id"].startswith("MOCK-")

    outbox = query_all(app, "SELECT * FROM email_outbox WHERE to_address = ?", ("zhangxiaoming@campus.edu.cn",))
    assert len(outbox) == 1


def test_cr2_02_review_approve_and_reject_both_channels(admin_client, app, make_activity):
    """CR2-02：审核批准与拒绝 → 两种渠道记录对应结果。"""
    activity = make_activity(title="CR2 审核活动", capacity=3, policy="review")
    student = app.test_client()

    login(student, "s1")
    student.post(f"/activities/{activity.activity_id}/register", follow_redirects=True)
    reg_s1 = query_one(
        app,
        "SELECT * FROM registrations WHERE activity_id = ? AND student_id = 's1'",
        (activity.activity_id,),
    )
    admin_client.post(
        f"/admin/approvals/{reg_s1['registration_id']}/approve", follow_redirects=True
    )

    login(student, "s2")
    student.post(f"/activities/{activity.activity_id}/register", follow_redirects=True)
    reg_s2 = query_one(
        app,
        "SELECT * FROM registrations WHERE activity_id = ? AND student_id = 's2'",
        (activity.activity_id,),
    )
    admin_client.post(
        f"/admin/approvals/{reg_s2['registration_id']}/reject", follow_redirects=True
    )

    approved_message = query_one(
        app,
        "SELECT * FROM messages WHERE student_id = 's1' AND category = 'registration_approved'",
    )
    rejected_message = query_one(
        app,
        "SELECT * FROM messages WHERE student_id = 's2' AND category = 'registration_rejected'",
    )
    assert approved_message is not None
    assert rejected_message is not None

    approve_mail = query_one(
        app,
        "SELECT * FROM email_deliveries WHERE student_id = 's1' AND subject LIKE '%审核通过%'",
    )
    reject_mail = query_one(
        app,
        "SELECT * FROM email_deliveries WHERE student_id = 's2' AND subject LIKE '%未通过%'",
    )
    assert approve_mail is not None
    assert reject_mail is not None
    assert approve_mail["status"] == "sent"
    assert reject_mail["status"] == "sent"


def test_cr2_03_email_failure_keeps_registration_and_logs(tmp_path):
    """CR2-03：模拟邮件失败 → 报名状态正确、错误有日志、站内消息仍送达。"""
    database = tmp_path / "cr2-failing.sqlite3"
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE": str(database),
            "SEED_DEMO_DATA": True,
            "EMAIL_GATEWAY": "failing",
        }
    )
    with app.app_context():
        container = get_container()
        admin = container.students.get("admin")
        activity = container.activity_service.create(
            admin,
            {
                "title": "CR2 邮件故障活动",
                "category": "测试",
                "location": "测试地点",
                "capacity": "2",
                "policy_type": "direct",
                "start_at": _future(),
                "description": "CR2 故障注入",
            },
        )

    client = app.test_client()
    login(client, "s1")
    response = client.post(
        f"/activities/{activity.activity_id}/register", follow_redirects=True
    )
    assert "报名成功" in response.get_data(as_text=True)

    registration = query_one(
        app,
        "SELECT status FROM registrations WHERE activity_id = ? AND student_id = 's1'",
        (activity.activity_id,),
    )
    assert registration["status"] == "approved"
    assert query_one(
        app,
        "SELECT COUNT(*) AS n FROM messages WHERE student_id = 's1' AND activity_id = ?",
        (activity.activity_id,),
    )["n"] == 1

    failed = query_one(
        app, "SELECT * FROM email_deliveries WHERE student_id = 's1' AND status = 'failed'"
    )
    assert failed is not None
    assert "SMTP" in failed["error"]
    assert query_one(app, "SELECT COUNT(*) AS n FROM email_outbox")["n"] == 0


def test_cr2_04_same_event_sends_only_one_email(client, app, make_activity):
    """CR2-04：重复发布同一业务事件 → 不重复生成邮件。"""
    activity = make_activity(title="CR2 幂等活动", capacity=3)
    login(client, "s1")
    client.post(f"/activities/{activity.activity_id}/register", follow_redirects=True)

    before_emails = query_one(app, "SELECT COUNT(*) AS n FROM email_deliveries")["n"]
    before_outbox = query_one(app, "SELECT COUNT(*) AS n FROM email_outbox")["n"]

    with app.app_context():
        container = get_container()
        detail = container.registrations.list_for_activity(activity.activity_id)[0]
        event = RegistrationApproved(
            registration=detail.registration,
            activity=detail.activity,
            student=detail.student,
            via="direct",
        )
        container.event_bus.publish(event)
        container.event_bus.publish(event)

    after_emails = query_one(app, "SELECT COUNT(*) AS n FROM email_deliveries")["n"]
    after_outbox = query_one(app, "SELECT COUNT(*) AS n FROM email_outbox")["n"]
    assert after_emails == before_emails + 1
    assert after_outbox == before_outbox + 1


def test_cr2_05_migration_from_v1_preserves_data(tmp_path):
    """CR2-05 / 迁移：v1 数据升级到 v2 后保留，且具备年级与邮件台账结构。"""
    database = tmp_path / "legacy-v1.sqlite3"
    connection = sqlite3.connect(database, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA_V1)
    connection.execute("CREATE TABLE schema_version (version INTEGER NOT NULL)")
    connection.execute("INSERT INTO schema_version (version) VALUES (1)")
    connection.execute(
        "INSERT INTO students (student_id, name, email, role) VALUES "
        "('s1', '张小明', 's1@campus.edu.cn', 'student')"
    )
    connection.execute(
        """
        INSERT INTO activities (activity_id, title, category, description, start_at,
                                location, capacity, policy_type, created_at, updated_at)
        VALUES ('ACT-LEGACY', '历史活动', '测试', '', '2030-01-01 10:00', '老地点', 2,
                'direct', '2026-11-01 10:00:00', '2026-11-01 10:00:00')
        """
    )
    connection.execute(
        """
        INSERT INTO registrations (registration_id, activity_id, student_id, status, note,
                                   created_at, updated_at)
        VALUES ('REG-LEGACY', 'ACT-LEGACY', 's1', 'approved', '',
                '2026-11-01 10:00:01', '2026-11-01 10:00:01')
        """
    )

    version = migrate(connection)
    assert version == 2
    assert connection.execute("SELECT version FROM schema_version").fetchone()[0] == 2

    student = connection.execute("SELECT * FROM students WHERE student_id = 's1'").fetchone()
    assert student["grade"] == 2  # 演示账号 s1 迁移为大二
    activity = connection.execute(
        "SELECT * FROM activities WHERE activity_id = 'ACT-LEGACY'"
    ).fetchone()
    assert activity["title"] == "历史活动"
    registration = connection.execute(
        "SELECT status FROM registrations WHERE registration_id = 'REG-LEGACY'"
    ).fetchone()
    assert registration["status"] == "approved"

    # v2 允许 grade_limited 报名方式
    connection.execute(
        """
        INSERT INTO activities (activity_id, title, category, description, start_at,
                                location, capacity, policy_type, created_at, updated_at)
        VALUES ('ACT-GRADE', '年级活动', '测试', '', '2030-02-01 10:00', '地点', 5,
                'grade_limited', '2026-11-02 10:00:00', '2026-11-02 10:00:00')
        """
    )
    assert connection.execute(
        "SELECT policy_type FROM activities WHERE activity_id = 'ACT-GRADE'"
    ).fetchone()["policy_type"] == "grade_limited"

    # 年级必须在 1—4
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO students (student_id, name, email, role, grade) "
            "VALUES ('s9', '非法年级', '', 'student', 0)"
        )

    # 邮件台账可用，且同一事件同一学生只允许一条
    connection.execute(
        """
        INSERT INTO email_deliveries
            (email_id, event_id, student_id, to_address, subject, body,
             status, error, sent_at, transport_id)
        VALUES ('MAIL-1', 'EVT-1', 's1', 's1@campus.edu.cn', '主题', '内容',
                'sent', NULL, '2026-11-02 10:00:00', 'MOCK-1')
        """
    )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO email_deliveries
                (email_id, event_id, student_id, to_address, subject, body,
                 status, error, sent_at, transport_id)
            VALUES ('MAIL-2', 'EVT-1', 's1', 's1@campus.edu.cn', '主题2', '内容2',
                    'sent', NULL, '2026-11-02 10:00:01', 'MOCK-2')
            """
        )
    connection.close()
