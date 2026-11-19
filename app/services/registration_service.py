"""报名服务：策略选择、公共规则校验、事务提交与事件发布。"""

from __future__ import annotations

import sqlite3

from ..clock import Clock
from ..db import transaction
from ..domain.errors import (
    DuplicateRegistration,
    InvalidTransition,
    NotFoundError,
    PermissionDenied,
    RegistrationRejected,
)
from ..domain.events import (
    RegistrationApproved,
    RegistrationCancelled,
    RegistrationSubmitted,
)
from ..domain.models import Registration, RegistrationStatus, Student, new_id
from ..domain.policies import PolicyRegistry, RegistrationContext
from ..repositories import ActivityRepository, RegistrationRepository, StudentRepository
from .event_bus import EventBus


class RegistrationService:
    def __init__(
        self,
        activities: ActivityRepository,
        students: StudentRepository,
        registrations: RegistrationRepository,
        policies: PolicyRegistry,
        publisher: EventBus,
        clock: Clock,
    ):
        self._activities = activities
        self._students = students
        self._registrations = registrations
        self._policies = policies
        self._publisher = publisher
        self._clock = clock

    def register(self, activity_id: str, student_id: str) -> Registration:
        activity = self._activities.get(activity_id)
        if activity is None:
            raise NotFoundError("活动不存在或已被删除")
        student = self._students.get(student_id)
        if student is None:
            raise NotFoundError("用户不存在")
        policy = self._policies.for_activity(activity)

        with transaction():
            existing = self._registrations.find_active(activity_id, student_id)
            approved = self._registrations.count_by_status(
                activity_id, RegistrationStatus.APPROVED
            )
            ctx = RegistrationContext(
                activity=activity,
                student=student,
                now=self._clock.now(),
                approved_count=approved,
                existing_active=existing,
            )
            decision = policy.evaluate(ctx)
            if not decision.allowed:
                raise RegistrationRejected(decision.reason)

            now = self._clock.now()
            registration = Registration(
                registration_id=new_id("REG"),
                activity_id=activity_id,
                student_id=student_id,
                status=decision.target_status,
                created_at=now,
                updated_at=now,
            )
            try:
                self._registrations.add(registration)
            except sqlite3.IntegrityError as exc:
                # 兜底：并发情况下唯一索引仍能阻止两条有效报名
                raise DuplicateRegistration("你已有该活动的有效报名，不能重复报名") from exc

        # 事务提交后再发通知：通知失败不会回滚报名，但会留痕
        if registration.status is RegistrationStatus.APPROVED:
            event = RegistrationApproved(
                registration=registration,
                activity=activity,
                student=student,
                via=policy.policy_type.value,
            )
        else:
            event = RegistrationSubmitted(
                registration=registration, activity=activity, student=student
            )
        self._publisher.publish(event)
        return registration

    def cancel(
        self,
        registration_id: str,
        actor: Student,
        reason: str = "",
    ) -> Registration:
        detail = self._registrations.get_detail(registration_id)
        if detail is None:
            raise NotFoundError("报名记录不存在")
        registration = detail.registration
        if not actor.is_admin and registration.student_id != actor.student_id:
            raise PermissionDenied("只能取消自己的报名")
        if not registration.is_active:
            raise InvalidTransition(f"当前状态为{registration.status.label}，不能取消")

        note = reason or ("管理员取消" if actor.is_admin else "学生主动取消")
        updated = registration.with_status(RegistrationStatus.CANCELLED, note=note)
        with transaction():
            self._registrations.update_status(updated)

        self._publisher.publish(
            RegistrationCancelled(
                registration=updated,
                activity=detail.activity,
                student=detail.student,
            )
        )
        return updated

    def list_mine(self, student_id: str):
        return self._registrations.list_for_student(student_id)

    def list_for_activity(self, activity_id: str):
        return self._registrations.list_for_activity(activity_id)
