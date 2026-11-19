"""CampusEvent 应用工厂。"""

from __future__ import annotations

from pathlib import Path

from flask import Flask

from . import db
from .seed import seed_demo_data


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="campusevent-dev-secret",
        DATABASE=str(Path(app.instance_path) / "campusevent.sqlite3"),
        EMAIL_GATEWAY="outbox",  # outbox | failing
        SEED_DEMO_DATA=True,
        # 与同主机上的其他 Flask 应用隔离，避免 session cookie 互相覆盖
        SESSION_COOKIE_NAME="campusevent_session",
    )
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    # 建表/迁移放在 init_app 内，保证每次启动都升级到当前 schema 版本
    db.init_app(app)

    with app.app_context():
        if app.config.get("SEED_DEMO_DATA"):
            seed_demo_data(db.get_db())

    from .web import register_web

    register_web(app)
    return app
