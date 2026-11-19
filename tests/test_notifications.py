"""通知机制测试：双渠道、失败留痕、幂等与事务边界。"""

from __future__ import annotations

from datetime import datetime, timedelta

from app import create_app
from app.dependencies import get_container
from app.domain.events import RegistrationApproved
from tests.helpers import login, query_all, query_one


def _future(days: int = 5) -> str:
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M")


def _create_activity_via_service(app, title="通知测试活动", capacity=2):
    with app.app_context():
        container = get_container()
        admin = container.students.get("admin")
        return container.activity_service.create(
            admin,
            {
                "title": title,
                "category": "测试",
                "location": "测试地点",
                "capacity": str(capacity),
                "policy_type": "direct",
                "start_at": _future(),
                "description": "通知测试",
            },
        )


def test_registration_notifies_both_channels(client, app, make_activity):
    activity = make_activity(title="双渠道通知活动", capacity=2)
    login(client, "s1")
    client.post(f"/activities/{activity.activity_id}/register", follow_redirects=True)

    messages = query_all(
        app,
        "SELECT * FROM messages WHERE student_id = 's1' AND activity_id = ?",
        (activity.activity_id,),
    )
    assert len(messages) == 1
    assert "报名成功" in messages[0]["content"]

    mails = query_all(
        app,
        "SELECT * FROM email_outbox WHERE to_address = ?",
        ("zhangxiaoming@campus.edu.cn",),
    )
    assert len(mails) == 1
    assert "报名成功" in mails[0]["body"]

    deliveries = query_all(
        app,
        "SELECT * FROM notification_deliveries WHERE student_id = 's1'",
    )
    assert len(deliveries) == 2
    assert {row["channel"] for row in deliveries} == {"站内消息", "邮件"}
    assert {row["status"] for row in deliveries} == {"sent"}


def test_email_failure_does_not_rollback_registration(tmp_path):
    database = tmp_path / "failing-email.sqlite3"
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE": str(database),
            "SEED_DEMO_DATA": True,
            "EMAIL_GATEWAY": "failing",
        }
    )
    activity = _create_activity_via_service(app, title="邮件故障活动")
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

    # 站内消息仍然送达
    message = query_one(
        app,
        "SELECT COUNT(*) AS n FROM messages WHERE student_id = 's1' AND activity_id = ?",
        (activity.activity_id,),
    )
    assert message["n"] == 1

    # 邮件失败留痕
    failed = query_one(
        app,
        "SELECT * FROM notification_deliveries WHERE student_id = 's1' AND channel = '邮件'",
    )
    assert failed is not None
    assert failed["status"] == "failed"
    assert "SMTP" in failed["error"]

    # 出件箱没有记录，因为故障发生在写入之前
    assert query_one(app, "SELECT COUNT(*) AS n FROM email_outbox")["n"] == 0


def test_same_event_is_not_notified_twice(client, app, make_activity):
    activity = make_activity(title="幂等通知活动", capacity=2)
    login(client, "s1")
    client.post(f"/activities/{activity.activity_id}/register", follow_redirects=True)

    before_messages = query_one(
        app,
        "SELECT COUNT(*) AS n FROM messages WHERE student_id = 's1' AND activity_id = ?",
        (activity.activity_id,),
    )["n"]
    before_mails = query_one(app, "SELECT COUNT(*) AS n FROM email_outbox")["n"]

    with app.app_context():
        container = get_container()
        detail = container.registrations.list_for_activity(activity.activity_id)[0]
        event = RegistrationApproved(
            registration=detail.registration,
            activity=detail.activity,
            student=detail.student,
            via="direct",
        )
        first = container.event_bus.publish(event)
        second = container.event_bus.publish(event)
        assert not first.has_failures
        assert not second.has_failures

    after_messages = query_one(
        app,
        "SELECT COUNT(*) AS n FROM messages WHERE student_id = 's1' AND activity_id = ?",
        (activity.activity_id,),
    )["n"]
    after_mails = query_one(app, "SELECT COUNT(*) AS n FROM email_outbox")["n"]
    assert after_messages == before_messages + 1
    assert after_mails == before_mails + 1
