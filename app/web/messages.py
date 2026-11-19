"""站内消息中心。"""

from __future__ import annotations

from flask import Blueprint, flash, g, redirect, render_template, url_for

from ..dependencies import get_container
from .security import login_required

bp = Blueprint("messages", __name__)


@bp.get("/messages")
@login_required
def list_messages():
    if g.user.is_admin:
        flash("管理员请到「通知台账」查看投递记录", "info")
        return redirect(url_for("admin.notifications"))
    container = get_container()
    items = container.messages.list_for_student(g.user.student_id)
    return render_template("messages/list.html", items=items)


@bp.post("/messages/read-all")
@login_required
def read_all():
    get_container().messages.mark_all_read(g.user.student_id)
    flash("已将全部站内消息标为已读", "success")
    return redirect(url_for("messages.list_messages"))
