"""轻量事件总线（观察者模式的落地形式）。

- 业务服务只负责 publish 事件，不知道有几个订阅者、也不知道是站内消息还是邮件；
- 每个订阅者独立 try/except，一个渠道失败不影响其他渠道，也不影响已提交的业务事务；
- 投递台账由订阅者写入数据库，属于"可观测性"，不参与业务事务。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Protocol

from ..domain.events import DomainEvent


class EventSubscriber(Protocol):
    name: str

    def supports(self, event: DomainEvent) -> bool: ...

    def handle(self, event: DomainEvent) -> None: ...


@dataclass
class DeliveryReport:
    delivered: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    @property
    def has_failures(self) -> bool:
        return bool(self.failed)


class EventBus:
    def __init__(self, subscribers: list[EventSubscriber], logger: logging.Logger | None = None):
        self._subscribers = list(subscribers)
        self._logger = logger or logging.getLogger(__name__)

    def publish(self, event: DomainEvent) -> DeliveryReport:
        report = DeliveryReport()
        for subscriber in self._subscribers:
            if not subscriber.supports(event):
                continue
            try:
                subscriber.handle(event)
            except Exception as exc:  # noqa: BLE001 - 通知失败不能中断业务
                report.failed.append((subscriber.name, str(exc)))
                self._logger.warning(
                    "通知订阅者 %s 处理事件 %s 失败：%s",
                    subscriber.name,
                    event.event_id,
                    exc,
                )
            else:
                report.delivered.append(subscriber.name)
        return report
