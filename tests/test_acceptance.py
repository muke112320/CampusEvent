"""初始版本核心验收用例 C1—C10（对应指导书 3.5 节）。

每个用例都通过 HTTP 页面操作，再从数据库核对结果，避免只验证返回值。
"""

from __future__ import annotations

from datetime import datetime, timedelta

from app import create_app
from tests.helpers import login, query_all, query_one


def _future(days: int = 6) -> str:
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M")


def test_c1_admin_creates_direct_activity(admin_client, app):
    """C1：管理员创建直接报名活动，容量 2。"""
    response = admin_client.post(
        "/admin/activities",
        data={
            "title": "C1 迎新志愿服务",
            "category": "志愿服务",
            "location": "大学生活动中心",
            "capacity": "2",
            "policy_type": "direct",
            "start_at": _future(),
            "description": "C1 用例创建",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "C1 迎新志愿服务" in response.get_data(as_text=True)
    row = query_one(app, "SELECT * FROM activities WHERE title = ?", ("C1 迎新志愿服务",))
    assert row is not None
    assert row["capacity"] == 2
    assert row["policy_type"] == "direct"


def test_c2_direct_registration_is_approved_and_notified(client, app, make_activity):
    """C2：学生 A 报名直接报名活动，立即通过并产生通知。"""
    activity = make_activity(title="C2 直接报名活动", capacity=2)
    login(client, "s1")
    response = client.post(
        f"/activities/{activity.activity_id}/register", follow_redirects=True
    )
    html = response.get_data(as_text=True)
    assert "报名成功" in html
    assert "已通过" in html

    registration = query_one(
        app,
        "SELECT * FROM registrations WHERE activity_id = ? AND student_id = 's1'",
        (activity.activity_id,),
    )
    assert registration["status"] == "approved"
    message = query_one(
        app,
        "SELECT * FROM messages WHERE student_id = 's1' AND activity_id = ?",
        (activity.activity_id,),
    )
    assert message is not None
    assert "报名成功" in message["content"]


def test_c3_duplicate_registration_rejected(client, app, make_activity):
    """C3：同一学生重复报名同一活动，拒绝且不产生第二条有效报名。"""
    activity = make_activity(title="C3 重复报名活动", capacity=5)
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


def test_c4_capacity_limit_blocks_registration(client, app, make_activity):
    """C4：容量 2，两位学生通过后第三位因名额不足失败。"""
    activity = make_activity(title="C4 名额有限活动", capacity=2)
    login(client, "s1")
    first = client.post(
        f"/activities/{activity.activity_id}/register", follow_redirects=True
    )
    assert "报名成功" in first.get_data(as_text=True)

    login(client, "s2")
    second = client.post(
        f"/activities/{activity.activity_id}/register", follow_redirects=True
    )
    assert "报名成功" in second.get_data(as_text=True)

    login(client, "s3")
    third = client.post(
        f"/activities/{activity.activity_id}/register", follow_redirects=True
    )
    assert "名额已满" in third.get_data(as_text=True)

    approved = query_one(
        app,
        "SELECT COUNT(*) AS n FROM registrations WHERE activity_id = ? AND status = 'approved'",
        (activity.activity_id,),
    )
    assert approved["n"] == 2


def test_c5_review_registration_is_pending(client, app, make_activity):
    """C5：审核型活动报名后为待审核，且待审核不占名额。"""
    activity = make_activity(
        title="C5 审核型活动", capacity=2, policy="review"
    )
    login(client, "s1")
    response = client.post(
        f"/activities/{activity.activity_id}/register", follow_redirects=True
    )
    assert "待审核" in response.get_data(as_text=True)
    registration = query_one(
        app,
        "SELECT * FROM registrations WHERE activity_id = ? AND student_id = 's1'",
        (activity.activity_id,),
    )
    assert registration["status"] == "pending"
    detail = client.get(f"/activities/{activity.activity_id}").get_data(as_text=True)
    assert "已通过" in detail
    assert "剩余名额" in detail


def test_c6_admin_approves_pending_registration(admin_client, app, make_activity):
    """C6：管理员批准待审核报名，状态变已通过并生成通知。"""
    activity = make_activity(title="C6 审批活动", capacity=3, policy="review")
    student = app.test_client()
    login(student, "s1")
    student.post(f"/activities/{activity.activity_id}/register", follow_redirects=True)
    registration = query_one(
        app,
        "SELECT * FROM registrations WHERE activity_id = ? AND student_id = 's1'",
        (activity.activity_id,),
    )
    assert registration["status"] == "pending"

    response = admin_client.post(
        f"/admin/approvals/{registration['registration_id']}/approve",
        follow_redirects=True,
    )
    assert "已批准" in response.get_data(as_text=True)
    updated = query_one(
        app,
        "SELECT status FROM registrations WHERE registration_id = ?",
        (registration["registration_id"],),
    )
    assert updated["status"] == "approved"
    message = query_one(
        app,
        "SELECT * FROM messages WHERE student_id = 's1' AND category = 'registration_approved'",
    )
    assert message is not None


def test_c7_admin_rejects_pending_registration(admin_client, app, make_activity):
    """C7：管理员拒绝待审核报名，状态变已拒绝并生成通知。"""
    activity = make_activity(title="C7 拒绝活动", capacity=3, policy="review")
    student = app.test_client()
    login(student, "s2")
    student.post(f"/activities/{activity.activity_id}/register", follow_redirects=True)
    registration = query_one(
        app,
        "SELECT * FROM registrations WHERE activity_id = ? AND student_id = 's2'",
        (activity.activity_id,),
    )
    response = admin_client.post(
        f"/admin/approvals/{registration['registration_id']}/reject",
        follow_redirects=True,
    )
    assert "已拒绝" in response.get_data(as_text=True)
    updated = query_one(
        app,
        "SELECT status FROM registrations WHERE registration_id = ?",
        (registration["registration_id"],),
    )
    assert updated["status"] == "rejected"
    message = query_one(
        app,
        "SELECT * FROM messages WHERE student_id = 's2' AND category = 'registration_rejected'",
    )
    assert message is not None


def test_c8_approval_fails_when_capacity_is_full(admin_client, app, make_activity):
    """C8：批准时名额已满，批准失败且不超出人数上限。"""
    activity = make_activity(title="C8 审批满员活动", capacity=1, policy="review")
    student_client = app.test_client()

    login(student_client, "s1")
    student_client.post(f"/activities/{activity.activity_id}/register", follow_redirects=True)
    reg_s1 = query_one(
        app,
        "SELECT * FROM registrations WHERE activity_id = ? AND student_id = 's1'",
        (activity.activity_id,),
    )

    login(student_client, "s2")
    student_client.post(f"/activities/{activity.activity_id}/register", follow_redirects=True)
    reg_s2 = query_one(
        app,
        "SELECT * FROM registrations WHERE activity_id = ? AND student_id = 's2'",
        (activity.activity_id,),
    )

    admin_client.post(
        f"/admin/approvals/{reg_s1['registration_id']}/approve", follow_redirects=True
    )
    response = admin_client.post(
        f"/admin/approvals/{reg_s2['registration_id']}/approve", follow_redirects=True
    )
    assert "名额已满" in response.get_data(as_text=True)

    approved = query_one(
        app,
        "SELECT COUNT(*) AS n FROM registrations WHERE activity_id = ? AND status = 'approved'",
        (activity.activity_id,),
    )
    assert approved["n"] == 1
    still_pending = query_one(
        app,
        "SELECT status FROM registrations WHERE registration_id = ?",
        (reg_s2["registration_id"],),
    )
    assert still_pending["status"] == "pending"


def test_c9_cancel_registration_releases_slot(client, app, make_activity):
    """C9：学生取消已通过报名，状态变已取消且统计同步变化。"""
    activity = make_activity(title="C9 取消活动", capacity=1)
    login(client, "s3")
    client.post(f"/activities/{activity.activity_id}/register", follow_redirects=True)
    registration = query_one(
        app,
        "SELECT * FROM registrations WHERE activity_id = ? AND student_id = 's3'",
        (activity.activity_id,),
    )
    assert registration["status"] == "approved"

    response = client.post(
        f"/registrations/{registration['registration_id']}/cancel",
        follow_redirects=True,
    )
    assert "已取消" in response.get_data(as_text=True)
    updated = query_one(
        app,
        "SELECT status FROM registrations WHERE registration_id = ?",
        (registration["registration_id"],),
    )
    assert updated["status"] == "cancelled"
    approved = query_one(
        app,
        "SELECT COUNT(*) AS n FROM registrations WHERE activity_id = ? AND status = 'approved'",
        (activity.activity_id,),
    )
    assert approved["n"] == 0


def test_c10_data_survives_restart(client, app, make_activity):
    """C10：重启应用（新建应用实例）后活动、报名与通知仍然存在。"""
    activity = make_activity(title="C10 持久化活动", capacity=2)
    login(client, "s1")
    client.post(f"/activities/{activity.activity_id}/register", follow_redirects=True)

    restarted = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE": app.config["DATABASE"],
            "SEED_DEMO_DATA": True,
        }
    )
    new_client = restarted.test_client()
    login(new_client, "s1")
    response = new_client.get("/my/registrations")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "C10 持久化活动" in html
    assert "已通过" in html
    assert "站内消息" in html
