"""管理员审批台与通知台账。"""

from __future__ import annotations

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from ..dependencies import get_container
from ..domain.errors import DomainError
from .security import admin_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.get("/approvals")
@admin_required
def approvals():
    container = get_container()
    activity_id = (request.args.get("activity_id") or "").strip() or None
    pending = container.registrations.list_pending(activity_id)
    activities = container.activity_service.list()
    stats = {
        activity.activity_id: container.activity_service.stats(activity)
        for activity in activities
    }
    return render_template(
        "admin/approvals.html",
        pending=pending,
        activities=activities,
        stats=stats,
        selected_activity=activity_id,
    )


@bp.post("/approvals/<registration_id>/approve")
@admin_required
def approve(registration_id: str):
    container = get_container()
    detail = container.registrations.get_detail(registration_id)
    try:
        container.approval_service.approve(registration_id, g.user)
    except DomainError as error:
        flash(error.message, "error")
    else:
        flash(f"已批准 {detail.student.name} 的报名申请", "success")
    return _back_to_approvals(request.form.get("activity_id"))


@bp.post("/approvals/<registration_id>/reject")
@admin_required
def reject(registration_id: str):
    container = get_container()
    detail = container.registrations.get_detail(registration_id)
    try:
        container.approval_service.reject(registration_id, g.user)
    except DomainError as error:
        flash(error.message, "error")
    else:
        flash(f"已拒绝 {detail.student.name} 的报名申请", "success")
    return _back_to_approvals(request.form.get("activity_id"))


def _back_to_approvals(activity_id: str | None):
    if activity_id:
        return redirect(url_for("admin.approvals", activity_id=activity_id))
    return redirect(url_for("admin.approvals"))


@bp.get("/notifications")
@admin_required
def notifications():
    container = get_container()
    return render_template(
        "admin/notifications.html",
        deliveries=container.deliveries.list_recent(),
        outbox=container.outbox.list_recent(),
        emails=container.email_deliveries.list_recent(),
        email_failed=container.email_deliveries.count_by_status("failed"),
        failed_count=container.deliveries.count_failed(),
    )
