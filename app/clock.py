"""可注入的时钟，便于测试"活动开始前/后"等时间相关规则。"""

from __future__ import annotations

from datetime import datetime
from typing import Callable


class Clock:
    def __init__(self, now_provider: Callable[[], datetime] | None = None):
        self._now_provider = now_provider or datetime.now

    def now(self) -> datetime:
        return self._now_provider()
