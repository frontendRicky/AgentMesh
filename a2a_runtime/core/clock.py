"""Clock utilities with an injectable Asia/Shanghai default."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

A2A_DEFAULT_TZ = timezone(timedelta(hours=8))


@dataclass(frozen=True)
class Clock:
    tz: timezone = A2A_DEFAULT_TZ

    def now(self) -> datetime:
        return datetime.now(self.tz)

    def now_iso(self) -> str:
        return self.now().isoformat(timespec="seconds")


@dataclass(frozen=True)
class FixedClock(Clock):
    fixed_at: datetime = datetime(2026, 1, 1, tzinfo=A2A_DEFAULT_TZ)

    def now(self) -> datetime:
        if self.fixed_at.tzinfo is None:
            return self.fixed_at.replace(tzinfo=self.tz)
        return self.fixed_at.astimezone(self.tz)


def parse_iso_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)
