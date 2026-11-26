"""模拟邮件发送器（change-v2 / CR-02）。

不连接真实 SMTP：每次发送都写入 `email_outbox`（模拟邮箱）与
`email_deliveries`（发送台账，记录收件人、主题、内容、状态、错误与时间）。

设计要点：
- 由 EmailNotificationSubscriber 调用，属于观察者侧渠道实现，业务服务不感知邮件；
- 发送失败只记录并抛出 NotificationError，由订阅者写入投递台账，报名事务已提交、不回滚；
- 以 (event_id, student_id) 唯一约束保证同一业务事件对同一学生只发一封。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import uuid4

from ..clock import Clock
from ..domain.errors import NotificationError
from ..domain.models import Student, new_id
from ..repositories import EmailDeliveryRepository, EmailOutboxRepository


@dataclass(frozen=True)
class EmailReceipt:
    """一次邮件发送的结果；duplicate=True 表示该事件已发送过，复用原记录。"""

    transport_id: str
    status: str
    duplicate: bool = False


class MockEmailSender:
    """教师/学生提供的 MockEmailSender：记录邮件而不真正投递。"""

    name = "mock"

    def __init__(
        self,
        outbox: EmailOutboxRepository,
        deliveries: EmailDeliveryRepository,
        clock: Clock,
        logger: logging.Logger | None = None,
        fail: bool = False,
    ):
        self._outbox = outbox
        self._deliveries = deliveries
        self._clock = clock
        self._logger = logger or logging.getLogger(__name__)
        self._fail = fail

    def send(
        self, event_id: str, student: Student, subject: str, body: str
    ) -> EmailReceipt:
        existing = self._deliveries.find_for_event(event_id, student.student_id)
        if existing is not None:
            self._logger.info(
                "跳过重复邮件：%s / %s（已记录 %s）",
                event_id,
                student.student_id,
                existing["status"],
            )
            return EmailReceipt(existing["transport_id"] or "", existing["status"], True)

        sent_at = self._clock.now()
        if self._fail:
            error = "SMTP 连接超时，邮件发送失败（MockEmailSender 故障注入）"
            self._record(event_id, student, subject, body, "failed", error, sent_at, None)
            raise NotificationError(error)
        if not student.email:
            error = "收件人邮箱为空，邮件未发送"
            self._record(event_id, student, subject, body, "failed", error, sent_at, None)
            raise NotificationError(error)

        transport_id = f"MOCK-{uuid4().hex[:10].upper()}"
        self._outbox.add(student.email, subject, body, transport_id)
        self._record(event_id, student, subject, body, "sent", None, sent_at, transport_id)
        self._logger.info("模拟邮件已发送：%s -> %s (%s)", subject, student.email, transport_id)
        return EmailReceipt(transport_id, "sent")

    def _record(
        self,
        event_id: str,
        student: Student,
        subject: str,
        body: str,
        status: str,
        error: str | None,
        sent_at,
        transport_id: str | None,
    ) -> None:
        self._deliveries.record(
            email_id=new_id("MAIL"),
            event_id=event_id,
            student_id=student.student_id,
            to_address=student.email,
            subject=subject,
            body=body,
            status=status,
            error=error,
            sent_at=sent_at,
            transport_id=transport_id,
        )
