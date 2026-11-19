"""应用容器：装配仓储、策略、事件总线与服务。

Web 层只依赖容器中的服务；测试也可以按需替换其中任一协作者
（例如把邮件网关换成故障注入实现）。
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from typing import Callable

from .clock import Clock
from .domain.policies import PolicyRegistry, default_policy_registry
from .repositories import (
    ActivityRepository,
    EmailOutboxRepository,
    MessageRepository,
    NotificationDeliveryRepository,
    RegistrationRepository,
    StudentRepository,
)
from .services.activity_service import ActivityService
from .services.approval_service import ApprovalService
from .services.email import EmailGateway, FailingEmailGateway, OutboxEmailGateway
from .services.event_bus import EventBus
from .services.notification_service import (
    NotificationContentBuilder,
    build_subscribers,
)
from .services.registration_service import RegistrationService


@dataclass
class Container:
    clock: Clock
    activities: ActivityRepository
    students: StudentRepository
    registrations: RegistrationRepository
    messages: MessageRepository
    outbox: EmailOutboxRepository
    deliveries: NotificationDeliveryRepository
    policies: PolicyRegistry
    event_bus: EventBus
    activity_service: ActivityService
    registration_service: RegistrationService
    approval_service: ApprovalService


def build_container(
    connection: sqlite3.Connection,
    *,
    now_provider: Callable | None = None,
    email_gateway: EmailGateway | None = None,
    logger: logging.Logger | None = None,
) -> Container:
    clock = Clock(now_provider)
    logger = logger or logging.getLogger("campusevent")

    activities = ActivityRepository(connection)
    students = StudentRepository(connection)
    registrations = RegistrationRepository(connection)
    messages = MessageRepository(connection)
    outbox = EmailOutboxRepository(connection)
    deliveries = NotificationDeliveryRepository(connection)

    policies = default_policy_registry()

    gateway = email_gateway or OutboxEmailGateway(outbox, logger)
    content_builder = NotificationContentBuilder()
    subscribers = build_subscribers(
        content_builder, messages, deliveries, gateway, clock, logger
    )
    event_bus = EventBus(list(subscribers), logger)

    return Container(
        clock=clock,
        activities=activities,
        students=students,
        registrations=registrations,
        messages=messages,
        outbox=outbox,
        deliveries=deliveries,
        policies=policies,
        event_bus=event_bus,
        activity_service=ActivityService(activities, registrations, clock),
        registration_service=RegistrationService(
            activities, students, registrations, policies, event_bus, clock
        ),
        approval_service=ApprovalService(registrations, event_bus, clock),
    )


def build_failing_email_container(connection: sqlite3.Connection) -> Container:
    """测试/演示辅助：邮件渠道必然失败，用于验证事务边界与留痕。"""
    return build_container(connection, email_gateway=FailingEmailGateway())
