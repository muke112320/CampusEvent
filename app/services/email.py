"""邮件通知网关。

真实部署可替换为 SMTP 网关；本项目默认使用"出件箱"实现，把邮件写入
email_outbox 表并在日志中输出，便于课程演示与自动化测试复现。
"""

from __future__ import annotations

import logging
from typing import Protocol
from uuid import uuid4

from ..domain.errors import NotificationError
from ..repositories import EmailOutboxRepository


class EmailGateway(Protocol):
    def send(self, to_address: str, subject: str, body: str) -> str: ...


class OutboxEmailGateway:
    """把邮件落库到出件箱，模拟 SMTP 已接收。"""

    name = "outbox"

    def __init__(self, outbox: EmailOutboxRepository, logger: logging.Logger | None = None):
        self._outbox = outbox
        self._logger = logger or logging.getLogger(__name__)

    def send(self, to_address: str, subject: str, body: str) -> str:
        if not to_address:
            raise NotificationError("收件人邮箱为空，邮件未发送")
        transport_id = f"SMTP-{uuid4().hex[:10].upper()}"
        self._outbox.add(to_address, subject, body, transport_id)
        self._logger.info("邮件已投递到出件箱：%s -> %s (%s)", subject, to_address, transport_id)
        return transport_id


class FailingEmailGateway:
    """故障注入网关：用于验证"通知失败不影响报名事务"以及失败留痕。"""

    name = "failing"

    def send(self, to_address: str, subject: str, body: str) -> str:  # noqa: ARG002
        raise NotificationError("SMTP 连接超时，邮件发送失败（故障注入）")
