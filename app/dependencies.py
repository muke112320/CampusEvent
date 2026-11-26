"""请求级依赖装配：把数据库连接、容器挂到 Flask 的 g 上。"""

from __future__ import annotations

from flask import current_app, g

from .container import Container, build_container
from .db import get_db


def get_container() -> Container:
    if "container" not in g:
        g.container = build_container(
            get_db(),
            fail_email=current_app.config.get("EMAIL_GATEWAY") == "failing",
            logger=current_app.logger,
        )
    return g.container
