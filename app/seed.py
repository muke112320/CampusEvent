"""演示数据：固定学生/管理员账号与若干活动，便于课堂验收。

日期相对"当前时间"生成，保证任何时间运行都有可报名的活动。
重复执行不会产生重复数据（按主键与数量判断）。
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta

from .db import transaction
from .domain.models import Activity, PolicyType, Role, Student
from .repositories import ActivityRepository, StudentRepository


def _at(day_offset: int, hour: int = 14) -> datetime:
    base = datetime.now() + timedelta(days=day_offset)
    return base.replace(hour=hour, minute=0, second=0, microsecond=0)


def _demo_students() -> list[Student]:
    return [
        Student("admin", "系统管理员", "admin@campus.edu.cn", Role.ADMIN),
        Student("s1", "张小明", "zhangxiaoming@campus.edu.cn"),
        Student("s2", "李小红", "lixiaohong@campus.edu.cn"),
        Student("s3", "王大力", "wangdali@campus.edu.cn"),
        Student("s4", "赵晓雨", "zhaoxiaoyu@campus.edu.cn"),
    ]


def _demo_activities() -> list[Activity]:
    now = datetime.now()
    rows = [
        {
            "id": "ACT-DEMO-01",
            "title": "迎新志愿者招募",
            "category": "志愿服务",
            "description": "面向全校招募迎新志愿者，协助新生报到、行李搬运与路线引导。名额有限，报满即止。",
            "start_at": _at(5),
            "location": "大学生活动中心 101",
            "capacity": 2,
            "policy": PolicyType.DIRECT,
        },
        {
            "id": "ACT-DEMO-02",
            "title": "校园歌手大赛初赛",
            "category": "文艺活动",
            "description": "一年一度的校园歌手大赛初赛，报名后由主办方审核参赛资格。",
            "start_at": _at(9),
            "location": "图书馆报告厅",
            "capacity": 3,
            "policy": PolicyType.REVIEW,
        },
        {
            "id": "ACT-DEMO-03",
            "title": "程序设计竞赛（校赛）",
            "category": "学科竞赛",
            "description": "个人赛，现场上机 3 小时，题目覆盖数据结构、算法与数据库。",
            "start_at": _at(14, hour=9),
            "location": "实验楼 B305",
            "capacity": 50,
            "policy": PolicyType.DIRECT,
        },
        {
            "id": "ACT-DEMO-04",
            "title": "摄影技巧讲座",
            "category": "讲座沙龙",
            "description": "校摄影协会指导老师讲解人像与风光摄影构图，需审核后参加。",
            "start_at": _at(3, hour=19),
            "location": "艺术楼 204",
            "capacity": 1,
            "policy": PolicyType.REVIEW,
        },
    ]
    return [
        Activity(
            activity_id=row["id"],
            title=row["title"],
            category=row["category"],
            description=row["description"],
            start_at=row["start_at"],
            location=row["location"],
            capacity=row["capacity"],
            policy_type=row["policy"],
            created_at=now,
            updated_at=now,
        )
        for row in rows
    ]


def seed_demo_data(connection: sqlite3.Connection) -> None:
    students = StudentRepository(connection)
    activities = ActivityRepository(connection)
    if students.count() == 0:
        with transaction():
            for student in _demo_students():
                students.add(student)
    if not activities.list():
        with transaction():
            for activity in _demo_activities():
                activities.add(activity)
