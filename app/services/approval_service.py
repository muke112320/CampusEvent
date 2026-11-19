"""审批服务：管理员批准/拒绝待审核报名，批准时再次检查名额。"""

from __future__ import annotations

from ..clock import Clock
from ..db import transaction
from ..domain.errors import CapacityExceeded, InvalidTransition, NotFoundError, PermissionDenied
from ..domain.events import RegistrationApproved, RegistrationRejected
from ..domain.models import Registration, RegistrationStatus, Student
from ..repositories import RegistrationRepository
from .event_bus import EventBus


class ApprovalService:
    def __init__(
        self,
        registrations: RegistrationRepository,
        publisher: EventBus,
        clock: Clock,
    ):
        self._registrations = registrations
        self._publisher = publisher
        self._clock = clock

    def approve(self, registration_id: str, actor: Student) -> Registration:
        self._require_admin(actor)
        detail = self._registrations.get_detail(registration_id)
        if detail is None:
            raise NotFoundError("报名记录不存在")
        registration = detail.registration
        if registration.status is not RegistrationStatus.PENDING:
            raise InvalidTransition(f"当前状态为{registration.status.label}，不能审批")
        activity = detail.activity

        with transaction():
            approved = self._registrations.count_by_status(
                activity.activity_id, RegistrationStatus.APPROVED
            )
            if approved >= activity.capacity:
                raise CapacityExceeded(
                    f"名额已满（上限 {activity.capacity} 人，已通过 {approved} 人），无法批准"
                )
            updated = registration.with_status(RegistrationStatus.APPROVED, note="管理员审核通过")
            self._registrations.update_status(updated)

        self._publisher.publish(
            RegistrationApproved(
                registration=updated,
                activity=activity,
                student=detail.student,
                via="review",
            )
        )
        return updated

    def reject(self, registration_id: str, actor: Student) -> Registration:
        self._require_admin(actor)
        detail = self._registrations.get_detail(registration_id)
        if detail is None:
            raise NotFoundError("报名记录不存在")
        registration = detail.registration
        if registration.status is not RegistrationStatus.PENDING:
            raise InvalidTransition(f"当前状态为{registration.status.label}，不能审批")

        updated = registration.with_status(RegistrationStatus.REJECTED, note="管理员审核拒绝")
        with transaction():
            self._registrations.update_status(updated)

        self._publisher.publish(
            RegistrationRejected(
                registration=updated,
                activity=detail.activity,
                student=detail.student,
            )
        )
        return updated

    @staticmethod
    def _require_admin(actor: Student) -> None:
        if not actor.is_admin:
            raise PermissionDenied("只有管理员可以审批报名")
