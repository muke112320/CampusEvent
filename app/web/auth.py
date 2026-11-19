"""登录/退出：固定演示账号，无密码（教学演示，不属于正式权限系统）。"""

from __future__ import annotations

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

from ..dependencies import get_container

bp = Blueprint("auth", __name__)


def _safe_next(target: str | None) -> str:
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return url_for("activities.index")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user is not None:
        return redirect(url_for("activities.index"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        container = get_container()
        user = container.students.get(username) if username else None
        if user is None:
            flash("账号不存在，请从下方演示账号中选择", "error")
        else:
            session.clear()
            session["user_id"] = user.student_id
            flash(f"欢迎，{user.name}（{user.role.label}）", "success")
            target = _safe_next(request.args.get("next"))
            # 子路径部署时 request.path 不含前缀，需要补回 SCRIPT_NAME
            if request.script_root and not target.startswith(request.script_root):
                target = request.script_root + target
            return redirect(target)

    accounts = get_container().students.list_all()
    return render_template("login.html", accounts=accounts)


@bp.post("/logout")
def logout():
    session.clear()
    flash("已退出登录", "info")
    return redirect(url_for("auth.login"))
