"""活动管理服务：管理员创建/编辑/删除活动，学生浏览活动。"""

from __future__ import annotations

from datetime import datetime

from ..clock import Clock
from ..db import transaction
from ..domain.errors import (
    DomainError,
    NotFoundError,
    PermissionDenied,
    ValidationError,
)
from ..domain.models import Activity, PolicyType, RegistrationStats, RegistrationStatus, Student, new_id
from ..repositories import ActivityRepository, RegistrationRepository

_DATE_FORMATS = ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S")


def parse_datetime(value: str) -> datetime:
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    raise ValidationError("活动时间格式不正确，示例：2026-12-01 14:00")


class ActivityService:
    def __init__(
        self,
        activities: ActivityRepository,
        registrations: RegistrationRepository,
        clock: Clock,
    ):
        self._activities = activities
        self._registrations = registrations
        self._clock = clock

    # ---------------- 查询 ----------------
    def list(self, keyword: str = "") -> list[Activity]:
        return self._activities.list(keyword.strip())

    def get(self, activity_id: str) -> Activity:
        activity = self._activities.get(activity_id)
        if activity is None:
            raise NotFoundError("活动不存在或已被删除")
        return activity

    def stats(self, activity: Activity) -> RegistrationStats:
        return self._registrations.stats(activity.activity_id, activity.capacity)

    # ---------------- 命令 ----------------
    def create(self, actor: Student, payload: dict) -> Activity:
        self._require_admin(actor)
        now = self._clock.now()
        data = self._validate(payload)
        if data["start_at"] <= now:
            raise ValidationError("活动开始时间必须晚于当前时间")
        activity = Activity(
            activity_id=new_id("ACT"),
            title=data["title"],
            category=data["category"],
            description=data["description"],
            start_at=data["start_at"],
            location=data["location"],
            capacity=data["capacity"],
            policy_type=data["policy_type"],
            created_at=now,
            updated_at=now,
        )
        with transaction():
            self._activities.add(activity)
        return activity

    def update(self, actor: Student, activity_id: str, payload: dict) -> Activity:
        self._require_admin(actor)
        activity = self.get(activity_id)
        data = self._validate(payload)

        approved = self._registrations.count_by_status(activity_id, RegistrationStatus.APPROVED)
        if approved > data["capacity"]:
            raise ValidationError(
                f"人数上限不能小于已通过人数（当前已通过 {approved} 人）"
            )
        if data["policy_type"] is not activity.policy_type and self._activities.count_registrations(activity_id) > 0:
            raise ValidationError("该活动已有报名记录，不能修改报名方式")

        updated = activity.with_updates(
            title=data["title"],
            category=data["category"],
            description=data["description"],
            start_at=data["start_at"],
            location=data["location"],
            capacity=data["capacity"],
            policy_type=data["policy_type"],
        )
        with transaction():
            self._activities.update(updated)
        return updated

    def delete(self, actor: Student, activity_id: str) -> None:
        """基线选择"拒绝删除并提示"，避免历史报名数据被级联清空。"""
        self._require_admin(actor)
        self.get(activity_id)
        count = self._activities.count_registrations(activity_id)
        if count > 0:
            raise DomainError(f"该活动已有 {count} 条报名记录，禁止删除；请先处理报名记录")
        with transaction():
            self._activities.delete(activity_id)

    # ---------------- 内部 ----------------
    @staticmethod
    def _require_admin(actor: Student) -> None:
        if not actor.is_admin:
            raise PermissionDenied("只有管理员可以管理活动")

    def _validate(self, payload: dict) -> dict:
        title = str(payload.get("title", "")).strip()
        category = str(payload.get("category", "")).strip()
        location = str(payload.get("location", "")).strip()
        description = str(payload.get("description", "")).strip()
        capacity_raw = str(payload.get("capacity", "")).strip()
        policy_raw = str(payload.get("policy_type", "")).strip()
        start_raw = str(payload.get("start_at", "")).strip()

        if not 1 <= len(title) <= 100:
            raise ValidationError("活动名称必填，长度 1—100 字")
        if not 1 <= len(category) <= 40:
            raise ValidationError("活动类型必填，长度 1—40 字")
        if not 1 <= len(location) <= 80:
            raise ValidationError("活动地点必填，长度 1—80 字")
        if len(description) > 1000:
            raise ValidationError("活动描述不能超过 1000 字")
        if not capacity_raw.isdigit():
            raise ValidationError("人数上限必须是正整数")
        capacity = int(capacity_raw)
        if not 1 <= capacity <= 500:
            raise ValidationError("人数上限应在 1—500 之间")
        try:
            policy_type = PolicyType(policy_raw)
        except ValueError as exc:
            raise ValidationError("请选择有效的报名方式") from exc
        if not start_raw:
            raise ValidationError("请填写活动开始时间")
        start_at = parse_datetime(start_raw)

        return {
            "title": title,
            "category": category,
            "location": location,
            "description": description,
            "capacity": capacity,
            "policy_type": policy_type,
            "start_at": start_at,
        }
