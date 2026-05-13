"""Base agent skeletons for Phase 3."""

from __future__ import annotations

from dataclasses import dataclass

from a2a_runtime.core.constants import Role
from a2a_runtime.core.paths import A2APaths


@dataclass
class AgentBase:
    paths: A2APaths
    role: Role

    def may_write_business_source(self) -> bool:
        return False
