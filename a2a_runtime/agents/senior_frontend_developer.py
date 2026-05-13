"""Senior Frontend Developer agent prompt facade."""

from __future__ import annotations

from dataclasses import dataclass

from a2a_runtime.agents.base import AgentBase
from a2a_runtime.core.constants import FileOperation, Role
from a2a_runtime.services.prompt_service import PromptService


@dataclass
class SeniorFrontendDeveloperAgent(AgentBase):
    role: Role = Role.DEVELOPER

    def generate_prompt(
        self,
        task_id: str,
        *,
        target_path: str | None = None,
        operation: FileOperation | str | None = None,
    ) -> str:
        return PromptService(self.paths).generate_developer_prompt(
            task_id,
            target_path=target_path,
            operation=operation,
        )
