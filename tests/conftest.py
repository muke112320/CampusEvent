from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app import create_app
from app.dependencies import get_container
from tests.helpers import login


@pytest.fixture
def app(tmp_path):
    database = tmp_path / "campusevent-test.sqlite3"
    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE": str(database),
            "SEED_DEMO_DATA": True,
        }
    )


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_client(client):
    login(client, "admin")
    return client


@pytest.fixture
def make_activity(app):
    """直接通过服务层创建活动，避免验收用例依赖建活动的界面。"""

    def _make(
        title: str = "测试活动",
        capacity: int = 2,
        policy: str = "direct",
        days: int = 5,
        **overrides,
    ):
        with app.app_context():
            container = get_container()
            admin = container.students.get("admin")
            payload = {
                "title": title,
                "category": overrides.pop("category", "测试类"),
                "location": overrides.pop("location", "测试地点"),
                "description": overrides.pop("description", "用于测试的活动"),
                "capacity": str(capacity),
                "policy_type": policy,
                "start_at": overrides.pop(
                    "start_at",
                    (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M"),
                ),
            }
            payload.update(overrides)
            return container.activity_service.create(admin, payload)

    return _make
