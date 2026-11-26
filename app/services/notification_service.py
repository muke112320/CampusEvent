"""通知：把领域事件翻译为站内消息与邮件。

观察者结构：
    RegistrationService --publish--> EventBus
                                      ├─ InSiteNotificationSubscriber -> messages 表
                                      └─ EmailNotificationSubscriber  -> email_outbox 表

两个渠道彼此独立：投递台账 notification_deliveries 以
(event_id, subscriber, student_id) 唯一，保证同一事件不会被重复通知。
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence

from ..clock import Clock
from ..domain.errors import NotificationError
from ..domain.events import (
    DomainEvent,
    RegistrationApproved,
    RegistrationCancelled,
    RegistrationRejected,
    RegistrationSubmitted,
)
from ..domain.models import Activity, Message, Student, new_id
from ..repositories import MessageRepository, NotificationDeliveryRepository
from .mock_email import MockEmailSender

NOTIFIABLE_EVENTS = (
    RegistrationSubmitted,
    RegistrationApproved,
    RegistrationRejected,
    RegistrationCancelled,
)


@dataclass(frozen=True)
class NotificationContent:
    event_id: str
    category: str
    subject: str
    body: str
    activity: Activity
    students: tuple[Student, ...]


class NotificationContentBuilder:
    """集中维护通知文案；渠道订阅者不重复写文案。"""

    def supports(self, event: DomainEvent) -> bool:
        return isinstance(event, NOTIFIABLE_EVENTS)

    def build(self, event: DomainEvent) -> NotificationContent | None:
        if not self.supports(event):
            return None
        activity = event.activity
        when = activity.start_at.strftime("%Y-%m-%d %H:%M")
        place = activity.location
        title = activity.title
        tail = f"活动时间：{when}；地点：{place}。"

        if isinstance(event, RegistrationSubmitted):
            return NotificationContent(
                event_id=event.event_id,
                category="registration_submitted",
                subject=f"报名申请已提交：{title}",
                body=f"你已提交活动「{title}」的报名申请，当前状态：待审核。{tail}管理员审核后将再次通知你。",
                activity=activity,
                students=(event.student,),
            )
        if isinstance(event, RegistrationApproved):
            if event.via == "review":
                prefix = "审核通过"
                body = f"你报名的活动「{title}」已通过管理员审核，当前状态：已通过。{tail}请按时参加。"
            else:
                prefix = "报名成功"
                body = f"报名成功！你已报名活动「{title}」，当前状态：已通过。{tail}请按时参加。"
            return NotificationContent(
                event_id=event.event_id,
                category="registration_approved",
                subject=f"{prefix}：{title}",
                body=body,
                activity=activity,
                students=(event.student,),
            )
        if isinstance(event, RegistrationRejected):
            return NotificationContent(
                event_id=event.event_id,
                category="registration_rejected",
                subject=f"报名未通过：{title}",
                body=f"很遗憾，你报名的活动「{title}」未通过审核，当前状态：已拒绝。{tail}",
                activity=activity,
                students=(event.student,),
            )
        if isinstance(event, RegistrationCancelled):
            return NotificationContent(
                event_id=event.event_id,
                category="registration_cancelled",
                subject=f"报名已取消：{title}",
                body=f"你已取消活动「{title}」的报名，当前状态：已取消。{tail}",
                activity=activity,
                students=(event.student,),
            )
        return None


class NotificationSubscriber(ABC):
    """通知订阅者模板：幂等 claim -> 投递 -> 记录成功/失败。"""

    name: str
    channel: str

    def __init__(
        self,
        builder: NotificationContentBuilder,
        deliveries: NotificationDeliveryRepository,
        clock: Clock,
        logger: logging.Logger | None = None,
    ):
        self._builder = builder
        self._deliveries = deliveries
        self._clock = clock
        self._logger = logger or logging.getLogger(__name__)

    def supports(self, event: DomainEvent) -> bool:
        return self._builder.supports(event)

    def handle(self, event: DomainEvent) -> None:
        content = self._builder.build(event)
        if content is None:
            return
        failures: list[str] = []
        for student in content.students:
            delivery_id = self._deliveries.claim(
                event_id=event.event_id,
                event_type=event.event_type,
                subscriber=self.name,
                channel=self.channel,
                student_id=student.student_id,
            )
            if delivery_id is None:
                # 同一事件已投递过：直接跳过，避免重复通知
                self._logger.info("跳过重复通知：%s / %s", event.event_id, student.student_id)
                continue
            try:
                self.deliver(student, content)
            except Exception as exc:  # noqa: BLE001 - 逐人隔离失败
                self._deliveries.mark(delivery_id, "failed", str(exc))
                failures.append(f"{student.name}：{exc}")
                self._logger.warning("通知投递失败（%s）：%s", self.channel, exc)
            else:
                self._deliveries.mark(delivery_id, "sent")
        if failures:
            raise NotificationError(f"{self.channel}通知部分失败：" + "；".join(failures))

    @abstractmethod
    def deliver(self, student: Student, content: NotificationContent) -> None:
        """真正的渠道投递。"""


class InSiteNotificationSubscriber(NotificationSubscriber):
    name = "in_site"
    channel = "站内消息"

    def __init__(self, messages: MessageRepository, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._messages = messages

    def deliver(self, student: Student, content: NotificationContent) -> None:
        self._messages.add(
            Message(
                message_id=new_id("MSG"),
                student_id=student.student_id,
                activity_id=content.activity.activity_id,
                category=content.category,
                content=content.body,
                created_at=self._clock.now(),
            )
        )


class EmailNotificationSubscriber(NotificationSubscriber):
    name = "email"
    channel = "邮件"

    def __init__(self, sender: MockEmailSender, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sender = sender

    def deliver(self, student: Student, content: NotificationContent) -> None:
        self._sender.send(content.event_id, student, content.subject, content.body)


def build_subscribers(
    builder: NotificationContentBuilder,
    messages: MessageRepository,
    deliveries: NotificationDeliveryRepository,
    sender: MockEmailSender,
    clock: Clock,
    logger: logging.Logger | None = None,
) -> Sequence[NotificationSubscriber]:
    """渠道装配点。新增渠道时只需在此追加一个订阅者。"""
    return [
        InSiteNotificationSubscriber(messages, builder, deliveries, clock, logger),
        EmailNotificationSubscriber(sender, builder, deliveries, clock, logger),
    ]
