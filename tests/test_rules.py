"""业务规则与边界条件测试（补充 C1—C10 未覆盖的分支）。"""

from __future__ import annotations

from datetime import datetime, timedelta

from app.domain.models import (
    Activity,
    PolicyType,
    RegistrationStatus,
    Student,
)
from app.domain.policies import (
    DirectRegistrationPolicy,
    RegistrationContext,
    ReviewRegistrationPolicy,
)
from tests.helpers import execute, login, query_all, query_one


def _ctx(activity: Activity, approved: int = 0, existing=None) -> RegistrationContext:
    return RegistrationContext(
        activity=activity,
        student=Student("s9", "测试学生", "s9@campus.edu.cn"),
        now=datetime.now(),
        approved_count=approved,
        existing_active=existing,
    )


def _activity(capacity: int = 2, policy: PolicyType = PolicyType.DIRECT) -> Activity:
    now = datetime.now()
    return Activity(
        activity_id="ACT-UNIT",
        title="单元测试活动",
        category="测试",
        start_at=now + timedelta(days=3),
        location="测试地点",
        capacity=capacity,
        policy_type=policy,
        created_at=now,
        updated_at=now,
    )


def test_direct_policy_denies_when_full():
    decision = DirectRegistrationPolicy().evaluate(_ctx(_activity(capacity=2), approved=2))
    assert decision.allowed is False
    assert "名额已满" in decision.reason


def test_direct_policy_approves_when_slots_available():
    decision = DirectRegistrationPolicy().evaluate(_ctx(_activity(capacity=2), approved=1))
    assert decision.allowed is True
    assert decision.target_status is RegistrationStatus.APPROVED


def test_review_policy_returns_pending_even_when_full():
    """待审核不占名额，所以满员时仍可提交申请（真正的闸门在审批）。"""
    decision = ReviewRegistrationPolicy().evaluate(
        _ctx(_activity(capacity=1, policy=PolicyType.REVIEW), approved=1)
    )
    assert decision.allowed is True
    assert decision.target_status is RegistrationStatus.PENDING


def test_registration_after_activity_start_is_rejected(client, app, make_activity):
    activity = make_activity(title="已开始活动", capacity=5)
    past = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
    execute(app, "UPDATE activities SET start_at = ? WHERE activity_id = ?", (past, activity.activity_id))

    login(client, "s1")
    response = client.post(
        f"/activities/{activity.activity_id}/register", follow_redirects=True
    )
    assert "活动已开始" in response.get_data(as_text=True)
    assert query_one(
        app, "SELECT COUNT(*) AS n FROM registrations WHERE activity_id = ?", (activity.activity_id,)
    )["n"] == 0


def test_create_activity_requires_title(admin_client, app):
    response = admin_client.post(
        "/admin/activities",
        data={
            "title": "   ",
            "category": "测试",
            "location": "地点",
            "capacity": "10",
            "policy_type": "direct",
            "start_at": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M"),
        },
    )
    assert response.status_code == 400
    assert "活动名称必填" in response.get_data(as_text=True)
    assert query_one(app, "SELECT COUNT(*) AS n FROM activities WHERE capacity = 10")["n"] == 0


def test_capacity_cannot_drop_below_approved(admin_client, app, make_activity):
    activity = make_activity(title="容量回退活动", capacity=3)
    for username in ("s1", "s2"):
        student = app.test_client()
        login(student, username)
        student.post(f"/activities/{activity.activity_id}/register", follow_redirects=True)

    response = admin_client.post(
        f"/admin/activities/{activity.activity_id}/edit",
        data={
            "title": activity.title,
            "category": activity.category,
            "location": activity.location,
            "capacity": "1",
            "policy_type": "direct",
            "start_at": activity.start_at.strftime("%Y-%m-%dT%H:%M"),
            "description": activity.description,
        },
    )
    assert response.status_code == 400
    assert "不能小于已通过人数" in response.get_data(as_text=True)


def test_policy_cannot_change_after_registrations(admin_client, app, make_activity):
    activity = make_activity(title="报名方式锁定活动", capacity=3)
    student = app.test_client()
    login(student, "s1")
    student.post(f"/activities/{activity.activity_id}/register", follow_redirects=True)

    response = admin_client.post(
        f"/admin/activities/{activity.activity_id}/edit",
        data={
            "title": activity.title,
            "category": activity.category,
            "location": activity.location,
            "capacity": "3",
            "policy_type": "review",
            "start_at": activity.start_at.strftime("%Y-%m-%dT%H:%M"),
            "description": activity.description,
        },
    )
    assert response.status_code == 400
    assert "不能修改报名方式" in response.get_data(as_text=True)


def test_activity_with_registrations_cannot_be_deleted(admin_client, app, make_activity):
    activity = make_activity(title="禁止删除活动", capacity=3)
    student = app.test_client()
    login(student, "s1")
    student.post(f"/activities/{activity.activity_id}/register", follow_redirects=True)

    response = admin_client.post(
        f"/admin/activities/{activity.activity_id}/delete", follow_redirects=True
    )
    assert "禁止删除" in response.get_data(as_text=True)
    assert query_one(
        app, "SELECT COUNT(*) AS n FROM activities WHERE activity_id = ?", (activity.activity_id,)
    )["n"] == 1


def test_rejected_registration_can_apply_again(admin_client, app, make_activity):
    activity = make_activity(title="拒绝后可重报活动", capacity=5, policy="review")
    student = app.test_client()
    login(student, "s1")
    student.post(f"/activities/{activity.activity_id}/register", follow_redirects=True)
    first = query_one(
        app,
        "SELECT * FROM registrations WHERE activity_id = ? AND student_id = 's1'",
        (activity.activity_id,),
    )
    admin_client.post(
        f"/admin/approvals/{first['registration_id']}/reject", follow_redirects=True
    )

    login(student, "s1")
    student.post(f"/activities/{activity.activity_id}/register", follow_redirects=True)
    rows = query_all(
        app,
        "SELECT status FROM registrations WHERE activity_id = ? AND student_id = 's1' ORDER BY created_at",
        (activity.activity_id,),
    )
    assert [row["status"] for row in rows] == ["rejected", "pending"]


def test_cancelled_registration_can_apply_again(admin_client, app, make_activity):
    activity = make_activity(title="取消后可重报活动", capacity=5)
    student = app.test_client()
    login(student, "s2")
    student.post(f"/activities/{activity.activity_id}/register", follow_redirects=True)
    registration = query_one(
        app,
        "SELECT * FROM registrations WHERE activity_id = ? AND student_id = 's2'",
        (activity.activity_id,),
    )
    student.post(
        f"/registrations/{registration['registration_id']}/cancel", follow_redirects=True
    )
    login(student, "s2")
    student.post(f"/activities/{activity.activity_id}/register", follow_redirects=True)

    statuses = [
        row["status"]
        for row in query_all(
            app,
            "SELECT status FROM registrations WHERE activity_id = ? AND student_id = 's2' ORDER BY created_at",
            (activity.activity_id,),
        )
    ]
    assert statuses == ["cancelled", "approved"]


def test_activity_search_filters_by_title(client, app, make_activity):
    make_activity(title="唯一搜索关键词活动")
    make_activity(title="完全不同的活动")
    login(client, "s1")
    html = client.get("/activities?q=唯一搜索关键词").get_data(as_text=True)
    assert "唯一搜索关键词活动" in html
    assert "完全不同的活动" not in html


def test_student_cannot_open_admin_pages(client, app):
    login(client, "s1")
    response = client.get("/admin/approvals")
    assert response.status_code == 403
    assert "没有访问权限" in response.get_data(as_text=True)


def test_admin_can_open_admin_pages(admin_client, app):
    response = admin_client.get("/admin/approvals")
    assert response.status_code == 200
    assert "审批台" in response.get_data(as_text=True)
