"""领域模型：只描述业务概念与不变量，不依赖 Flask、SQLite 或界面。

设计说明见 docs/03_UML类图.md。模型对象为不可变 dataclass，
状态流转通过服务层生成新实例完成，避免"随手改字段"绕过业务规则。
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum
from uuid import uuid4


class Role(str, Enum):
    """系统只有两类固定演示角色，不做注册与复杂权限。"""

    STUDENT = "student"
    ADMIN = "admin"

    @property
    def label(self) -> str:
        return {"student": "学生", "admin": "管理员"}[self.value]


class PolicyType(str, Enum):
    """报名方式（策略标识）。值同时持久化在 activities.policy_type 中。"""

    DIRECT = "direct"
    REVIEW = "review"

    @property
    def label(self) -> str:
        return {"direct": "直接报名", "review": "管理员审核"}[self.value]


class RegistrationStatus(str, Enum):
    """报名状态。有效状态（占用/申请中）由 is_active 判定。"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

    @property
    def label(self) -> str:
        return {
            "pending": "待审核",
            "approved": "已通过",
            "rejected": "已拒绝",
            "cancelled": "已取消",
        }[self.value]

    @property
    def is_active(self) -> bool:
        """待审核与已通过属于"有效报名"，同一学生同一活动只允许一条。"""
        return self in (RegistrationStatus.PENDING, RegistrationStatus.APPROVED)


def new_id(prefix: str) -> str:
    """生成可读的短业务 ID，例如 ACT-3F9A2C1B。"""
    return f"{prefix}-{uuid4().hex[:8].upper()}"


@dataclass(frozen=True)
class Student:
    student_id: str
    name: str
    email: str
    role: Role = Role.STUDENT

    @property
    def is_admin(self) -> bool:
        return self.role is Role.ADMIN


@dataclass(frozen=True)
class Activity:
    """校园活动。capacity 表示人数上限，并非"剩余名额"。"""

    activity_id: str
    title: str
    category: str
    start_at: datetime
    location: str
    capacity: int
    policy_type: PolicyType
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def with_updates(self, **changes) -> "Activity":
        return replace(self, updated_at=datetime.now(), **changes)

    def is_open_for_registration(self, now: datetime) -> bool:
        """活动开始前允许报名；开始后关闭入口。"""
        return now < self.start_at


@dataclass(frozen=True)
class Registration:
    registration_id: str
    activity_id: str
    student_id: str
    status: RegistrationStatus
    created_at: datetime
    updated_at: datetime
    note: str = ""

    @property
    def is_active(self) -> bool:
        return self.status.is_active

    def with_status(self, status: RegistrationStatus, note: str = "") -> "Registration":
        return replace(self, status=status, note=note, updated_at=datetime.now())


@dataclass(frozen=True)
class Message:
    """站内消息：报名/审核结果的持久化通知。"""

    message_id: str
    student_id: str
    activity_id: str | None
    category: str
    content: str
    created_at: datetime
    is_read: bool = False

    @classmethod
    def new(cls, student_id: str, activity_id: str | None, category: str, content: str) -> "Message":
        return cls(
            message_id=new_id("MSG"),
            student_id=student_id,
            activity_id=activity_id,
            category=category,
            content=content,
            created_at=datetime.now(),
        )


@dataclass(frozen=True)
class RegistrationStats:
    """按活动统计：已通过数、待审核数、剩余名额。"""

    activity_id: str
    capacity: int
    approved: int
    pending: int

    @property
    def remaining(self) -> int:
        return max(self.capacity - self.approved, 0)

    @property
    def is_full(self) -> bool:
        return self.approved >= self.capacity
