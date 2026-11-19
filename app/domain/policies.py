"""报名策略：策略模式 + 模板方法。

`RegistrationPolicy.evaluate` 是稳定的模板方法，负责所有报名方式都必须遵守的
公共规则（活动时间、重复有效报名）；`decide` 是变化点，由具体策略决定
"名额已满时怎么办、报名后进入什么状态"。

因此新增一种报名方式 = 新增一个策略类 + 注册一行，不需要在
RegistrationService 中写 if/elif 分支。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from .errors import ActivityClosed, DuplicateRegistration, ValidationError
from .models import Activity, PolicyType, Registration, RegistrationStatus, Student


@dataclass(frozen=True)
class RegistrationContext:
    """一次报名判定的完整输入，避免策略内部再访问仓储。"""

    activity: Activity
    student: Student
    now: datetime
    approved_count: int
    existing_active: Registration | None

    @property
    def remaining_slots(self) -> int:
        return max(self.activity.capacity - self.approved_count, 0)

    @property
    def is_full(self) -> bool:
        return self.remaining_slots <= 0


@dataclass(frozen=True)
class PolicyDecision:
    """策略结论：允许则给出报名落地状态，拒绝则给出面向用户的原因。"""

    allowed: bool
    target_status: RegistrationStatus | None = None
    reason: str = ""

    @classmethod
    def approve(cls, status: RegistrationStatus) -> "PolicyDecision":
        return cls(allowed=True, target_status=status)

    @classmethod
    def deny(cls, reason: str) -> "PolicyDecision":
        return cls(allowed=False, reason=reason)


class RegistrationPolicy(ABC):
    """报名规则抽象。子类只实现 decide，公共校验不可被绕过。"""

    policy_type: PolicyType
    display_name: str
    description: str

    def evaluate(self, ctx: RegistrationContext) -> PolicyDecision:
        # ---- 公共规则（所有报名方式一致）----
        if not ctx.activity.is_open_for_registration(ctx.now):
            raise ActivityClosed("活动已开始，不能再报名")
        if ctx.existing_active is not None:
            raise DuplicateRegistration(
                f"你已有一条第 {ctx.existing_active.status.label} 的报名，不能重复报名"
            )
        return self.decide(ctx)

    @abstractmethod
    def decide(self, ctx: RegistrationContext) -> PolicyDecision:
        """策略变化点：处理名额与落地状态。"""


class DirectRegistrationPolicy(RegistrationPolicy):
    """直接报名：名额充足则立即通过，满员则拒绝。"""

    policy_type = PolicyType.DIRECT
    display_name = "直接报名"
    description = "名额充足时报名立即生效，无需管理员审核；满员后拒绝新报名。"

    def decide(self, ctx: RegistrationContext) -> PolicyDecision:
        if ctx.is_full:
            return PolicyDecision.deny(f"名额已满（上限 {ctx.activity.capacity} 人），报名失败")
        return PolicyDecision.approve(RegistrationStatus.APPROVED)


class ReviewRegistrationPolicy(RegistrationPolicy):
    """审核报名：先进入待审核，待审核不占名额，由管理员批准或拒绝。"""

    policy_type = PolicyType.REVIEW
    display_name = "管理员审核"
    description = "报名先进入待审核，由管理员批准；批准时再次检查名额。"

    def decide(self, ctx: RegistrationContext) -> PolicyDecision:
        # 待审核不占用名额，因此即使当前已满也允许提交申请；
        # 真正的容量闸门在审批环节（ApprovalService）再次校验。
        return PolicyDecision.approve(RegistrationStatus.PENDING)


class PolicyRegistry:
    """策略注册表：按活动的 policy_type 选择具体策略。"""

    def __init__(self, policies: list[RegistrationPolicy]):
        self._policies = {policy.policy_type: policy for policy in policies}

    def for_activity(self, activity: Activity) -> RegistrationPolicy:
        policy = self._policies.get(activity.policy_type)
        if policy is None:
            raise ValidationError(f"不支持的报名方式：{activity.policy_type.value}")
        return policy

    def get(self, policy_type: PolicyType) -> RegistrationPolicy | None:
        return self._policies.get(policy_type)

    def has(self, policy_type: PolicyType) -> bool:
        return policy_type in self._policies

    def all(self) -> list[RegistrationPolicy]:
        # 保持稳定顺序，供界面下拉框使用
        order = [PolicyType.DIRECT, PolicyType.REVIEW]
        return [self._policies[t] for t in order if t in self._policies]


def default_policy_registry() -> PolicyRegistry:
    """基线版本支持两种报名方式。"""
    return PolicyRegistry([DirectRegistrationPolicy(), ReviewRegistrationPolicy()])
