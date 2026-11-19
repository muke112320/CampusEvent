"""Web 层装配：蓝图、模板过滤器、错误页与登录态加载。"""

from __future__ import annotations

from datetime import datetime

from flask import Flask, flash, g, redirect, render_template, request, session, url_for

from ..dependencies import get_container
from ..domain.errors import DomainError

CATEGORY_LABELS = {
    "registration_submitted": "报名待审核",
    "registration_approved": "报名通过",
    "registration_rejected": "报名未通过",
    "registration_cancelled": "报名已取消",
}

EVENT_LABELS = {
    "RegistrationSubmitted": "报名已提交",
    "RegistrationApproved": "报名已通过",
    "RegistrationRejected": "报名被拒绝",
    "RegistrationCancelled": "报名已取消",
}


def _format_datetime(value) -> str:
    if not value:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    return value.strftime("%Y-%m-%d %H:%M")


def _format_date(value: datetime | None) -> str:
    return value.strftime("%Y-%m-%d") if value else ""


def _format_input(value: datetime | None) -> str:
    return value.strftime("%Y-%m-%dT%H:%M") if value else ""


def register_web(app: Flask) -> None:
    from . import activities, admin, auth, messages, registrations

    app.register_blueprint(auth.bp)
    app.register_blueprint(activities.bp)
    app.register_blueprint(registrations.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(messages.bp)

    app.jinja_env.filters["dt"] = _format_datetime
    app.jinja_env.filters["date"] = _format_date
    app.jinja_env.filters["dt_input"] = _format_input
    app.jinja_env.filters["category_label"] = lambda key: CATEGORY_LABELS.get(key, key)
    app.jinja_env.filters["event_label"] = lambda key: EVENT_LABELS.get(key, key)

    @app.before_request
    def load_logged_in_user() -> None:
        if request.endpoint == "static":
            return
        user_id = session.get("user_id")
        g.user = None
        g.unread = 0
        if user_id:
            container = get_container()
            g.user = container.students.get(user_id)
            if g.user is not None and not g.user.is_admin:
                g.unread = container.messages.unread_count(user_id)

    @app.context_processor
    def inject_globals() -> dict:
        return {
            "current_year": datetime.now().year,
            "now": datetime.now(),
            "categories": CATEGORY_LABELS,
        }

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(DomainError)
    def domain_error(error: DomainError):
        """兜底：未被路由捕获的业务异常转换为中文提示，不暴露堆栈。"""
        flash(error.message, "error")
        return redirect(request.referrer or url_for("activities.index"))

    @app.errorhandler(500)
    def server_error(_error):  # pragma: no cover - 仅用于演示容错
        return render_template("errors/500.html"), 500
