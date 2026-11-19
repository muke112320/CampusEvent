"""报名、取消报名与学生"我的报名"。"""

from __future__ import annotations

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from ..dependencies import get_container
from ..domain.errors import DomainError
from ..domain.models import RegistrationStatus
from .security import login_required

bp = Blueprint("registrations", __name__)


@bp.post("/activities/<activity_id>/register")
@login_required
def register(activity_id: str):
    if g.user.is_admin:
        flash("管理员账号不参与报名，请切换学生账号演示", "warning")
        return redirect(url_for("activities.detail", activity_id=activity_id))

    container = get_container()
    try:
        registration = container.registration_service.register(activity_id, g.user.student_id)
    except DomainError as error:
        flash(error.message, "error")
    else:
        if registration.status is RegistrationStatus.APPROVED:
            flash("报名成功，当前状态：已通过", "success")
        else:
            flash("报名申请已提交，当前状态：待审核，请等待管理员审批", "success")
    return redirect(url_for("activities.detail", activity_id=activity_id))


@bp.post("/registrations/<registration_id>/cancel")
@login_required
def cancel(registration_id: str):
    container = get_container()
    detail = container.registrations.get_detail(registration_id)
    try:
        container.registration_service.cancel(registration_id, g.user)
    except DomainError as error:
        flash(error.message, "error")
    else:
        flash("已取消报名，名额已释放", "success")

    redirect_to = request.form.get("next")
    if redirect_to and redirect_to.startswith("/") and not redirect_to.startswith("//"):
        return redirect(redirect_to)
    if detail is not None:
        return redirect(url_for("activities.detail", activity_id=detail.activity.activity_id))
    return redirect(url_for("registrations.mine"))


@bp.get("/my/registrations")
@login_required
def mine():
    if g.user.is_admin:
        return redirect(url_for("activities.index"))
    container = get_container()
    details = container.registration_service.list_mine(g.user.student_id)
    return render_template("registrations/mine.html", details=details)
