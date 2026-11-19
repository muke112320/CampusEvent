"""为演示/截图准备一组真实报名数据（可重复执行，重复报名会被跳过）。

用法：python tools/demo_data.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# 允许从项目根目录直接执行：python tools/demo_data.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.dependencies import get_container
from app.domain.errors import DomainError


def main() -> None:
    app = create_app()
    with app.app_context():
        container = get_container()
        activities = {activity.title: activity for activity in container.activity_service.list()}
        plan = [
            ("s1", "迎新志愿者招募"),
            ("s2", "校园歌手大赛初赛"),
            ("s3", "校园歌手大赛初赛"),
            ("s1", "摄影技巧讲座"),
            ("s2", "程序设计竞赛（校赛）"),
        ]
        for username, title in plan:
            activity = activities.get(title)
            if activity is None:
                print(f"skip: activity missing {title}")
                continue
            try:
                registration = container.registration_service.register(
                    activity.activity_id, username
                )
                print(f"{username} -> {title}: {registration.status.label}")
            except DomainError as error:
                print(f"{username} -> {title}: skip ({error.message})")


if __name__ == "__main__":
    main()
