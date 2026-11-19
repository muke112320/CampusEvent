"""领域事件。

事件是"已发生的业务事实"的不可变快照，携带渲染通知所需的全部数据，
因此订阅者不需要回查数据库，也就不会在通知阶段反向依赖业务服务。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from .models import Activity, Registration, Student


def _event_id() -> str:
    return f"EVT-{uuid4().hex}"


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """事件基类。event_id 用于通知幂等（同一事件不重复投递）。"""

    event_id: str = field(default_factory=_event_id)
    occurred_at: datetime = field(default_factory=datetime.now)

    @property
    def event_type(self) -> str:
        return type(self).__name__


@dataclass(frozen=True, kw_only=True)
class RegistrationSubmitted(DomainEvent):
    """报名已提交但需审核（待审核）。"""

    registration: Registration
    activity: Activity
    student: Student


@dataclass(frozen=True, kw_only=True)
class RegistrationApproved(DomainEvent):
    """报名已通过：直接报名即时通过，或管理员审核通过。"""

    registration: Registration
    activity: Activity
    student: Student
    via: str = "direct"  # direct / review


@dataclass(frozen=True, kw_only=True)
class RegistrationRejected(DomainEvent):
    """报名被管理员拒绝。"""

    registration: Registration
    activity: Activity
    student: Student


@dataclass(frozen=True, kw_only=True)
class RegistrationCancelled(DomainEvent):
    """学生主动取消报名。"""

    registration: Registration
    activity: Activity
    student: Student
