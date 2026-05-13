"""Architect agent prompt facade."""

from __future__ import annotations

from dataclasses import dataclass

from a2a_runtime.agents.base import AgentBase
from a2a_runtime.core.constants import Role
from a2a_runtime.services.prompt_service import PromptService


@dataclass
class ArchitectAgent(AgentBase):
    role: Role = Role.ARCHITECT

    def generate_prompt(self, task_id: str) -> str:
        return PromptService(self.paths).generate_architect_prompt(task_id)
