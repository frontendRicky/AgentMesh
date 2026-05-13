"""QA Tester agent prompt facade."""

from __future__ import annotations

from dataclasses import dataclass

from a2a_runtime.agents.base import AgentBase
from a2a_runtime.core.constants import Role
from a2a_runtime.services.prompt_service import PromptService


@dataclass
class QATesterAgent(AgentBase):
    role: Role = Role.QA

    def generate_prompt(self, task_id: str) -> str:
        return PromptService(self.paths).generate_qa_prompt(task_id)
