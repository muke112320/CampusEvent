"""领域异常。

服务层只抛出这些异常，Web 层负责翻译为中文提示，避免把 sqlite3 / ValueError
等实现细节直接暴露给用户。异常自带面向用户的 message。
"""

from __future__ import annotations


class DomainError(Exception):
    """所有可预期业务错误的基类。"""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ValidationError(DomainError):
    """输入不合法：字段缺失、格式错误、超长、容量非法等。"""


class NotFoundError(DomainError):
    """实体不存在。"""


class PermissionDenied(DomainError):
    """越权操作：学生访问管理功能，或取消他人报名。"""


class ActivityClosed(DomainError):
    """活动已开始或已取消，不能继续报名。"""


class DuplicateRegistration(DomainError):
    """同一学生同一活动已存在待审核/已通过的有效报名。"""


class RegistrationRejected(DomainError):
    """策略判定不允许报名（例如直接报名遇到满员）。"""


class CapacityExceeded(DomainError):
    """名额已满：直接报名被拒绝，或审批时再次检查失败。"""


class InvalidTransition(DomainError):
    """当前状态不允许执行该操作（例如取消已拒绝报名）。"""


class NotificationError(DomainError):
    """通知投递失败。业务事务已提交，此错误只用于记录与告警。"""
