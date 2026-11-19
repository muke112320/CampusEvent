"""请求级依赖装配：把数据库连接、容器挂到 Flask 的 g 上。"""

from __future__ import annotations

from flask import current_app, g

from .container import Container, build_container
from .db import get_db
from .services.email import FailingEmailGateway


def get_container() -> Container:
    if "container" not in g:
        gateway = None
        if current_app.config.get("EMAIL_GATEWAY") == "failing":
            gateway = FailingEmailGateway()
        g.container = build_container(
            get_db(), email_gateway=gateway, logger=current_app.logger
        )
    return g.container
