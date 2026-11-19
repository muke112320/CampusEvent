"""活动浏览、详情与管理员活动维护。"""

from __future__ import annotations

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from ..dependencies import get_container
from ..domain.errors import DomainError
from .security import admin_required, login_required

bp = Blueprint("activities", __name__)


@bp.get("/")
@login_required
def home():
    return redirect(url_for("activities.index"))


@bp.get("/activities")
@login_required
def index():
    container = get_container()
    keyword = (request.args.get("q") or "").strip()
    activities = container.activity_service.list(keyword)
    stats = {
        activity.activity_id: container.activity_service.stats(activity)
        for activity in activities
    }
    my_registrations = {}
    if not g.user.is_admin:
        for activity in activities:
            my_registrations[activity.activity_id] = container.registrations.find_latest(
                activity.activity_id, g.user.student_id
            )
    return render_template(
        "activities/list.html",
        activities=activities,
        stats=stats,
        my_registrations=my_registrations,
        keyword=keyword,
    )


@bp.get("/activities/<activity_id>")
@login_required
def detail(activity_id: str):
    container = get_container()
    try:
        activity = container.activity_service.get(activity_id)
    except DomainError as error:
        flash(error.message, "error")
        return redirect(url_for("activities.index"))

    stats = container.activity_service.stats(activity)
    my_registration = None
    participants = []
    if g.user.is_admin:
        participants = container.registrations.list_for_activity(activity_id)
    else:
        my_registration = container.registrations.find_latest(activity_id, g.user.student_id)

    return render_template(
        "activities/detail.html",
        activity=activity,
        stats=stats,
        my_registration=my_registration,
        participants=participants,
    )


@bp.get("/admin/activities/new")
@admin_required
def new():
    return render_template(
        "activities/form.html",
        activity=None,
        form={},
        policies=get_container().policies.all(),
        mode="create",
    )


@bp.post("/admin/activities")
@admin_required
def create():
    container = get_container()
    form = request.form.to_dict()
    try:
        activity = container.activity_service.create(g.user, form)
    except DomainError as error:
        flash(error.message, "error")
        return (
            render_template(
                "activities/form.html",
                activity=None,
                form=form,
                policies=container.policies.all(),
                mode="create",
            ),
            400,
        )
    flash(f"活动「{activity.title}」创建成功", "success")
    return redirect(url_for("activities.detail", activity_id=activity.activity_id))


@bp.get("/admin/activities/<activity_id>/edit")
@admin_required
def edit(activity_id: str):
    container = get_container()
    try:
        activity = container.activity_service.get(activity_id)
    except DomainError as error:
        flash(error.message, "error")
        return redirect(url_for("activities.index"))
    return render_template(
        "activities/form.html",
        activity=activity,
        form={},
        policies=container.policies.all(),
        mode="edit",
    )


@bp.post("/admin/activities/<activity_id>/edit")
@admin_required
def update(activity_id: str):
    container = get_container()
    form = request.form.to_dict()
    try:
        activity = container.activity_service.update(g.user, activity_id, form)
    except DomainError as error:
        flash(error.message, "error")
        current = container.activities.get(activity_id)
        return (
            render_template(
                "activities/form.html",
                activity=current,
                form=form,
                policies=container.policies.all(),
                mode="edit",
            ),
            400,
        )
    flash("活动信息已更新", "success")
    return redirect(url_for("activities.detail", activity_id=activity.activity_id))


@bp.post("/admin/activities/<activity_id>/delete")
@admin_required
def delete(activity_id: str):
    container = get_container()
    try:
        container.activity_service.delete(g.user, activity_id)
    except DomainError as error:
        flash(error.message, "error")
        return redirect(url_for("activities.detail", activity_id=activity_id))
    flash("活动已删除", "success")
    return redirect(url_for("activities.index"))


@bp.app_template_global()
def policy_options():
    """模板中读取策略清单，用于说明卡片。"""
    return get_container().policies.all()
