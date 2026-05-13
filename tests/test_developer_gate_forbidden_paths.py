from __future__ import annotations

import unittest

from a2a_runtime.core.constants import FileOperation, GateFailureType
from a2a_runtime.models.file_change_plan import FileChangePlan, FileChangePlanEntry
from a2a_runtime.services.gate_service import GateService

from tests.test_developer_gate import make_state


def plan(path: str, *, owner: str = "developer") -> FileChangePlan:
    return FileChangePlan(
        [
            FileChangePlanEntry(
                path=path,
                operation=FileOperation.MODIFY,
                allowed=True,
                reason="planned",
                risk="high",
                owner=owner,
            ),
        ],
    )


class DeveloperGateForbiddenPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = GateService()

    def assert_forbidden(self, path: str, expected_condition: str) -> None:
        result = self.service.check_developer_write(
            state=make_state(),
            target_path=path,
            operation="modify",
            file_change_plan=plan(path),
        )
        self.assertFalse(result.allowed)
        self.assertEqual(result.failure_type, GateFailureType.RISK_DECISION_REQUIRED)
        self.assertIn(expected_condition, result.failed_conditions)

    def test_monorepo_package_json_forbidden(self) -> None:
        self.assert_forbidden("packages/foo/package.json", "forbidden dependency file")

    def test_subproject_package_json_forbidden(self) -> None:
        self.assert_forbidden("subproject/package.json", "forbidden dependency file")

    def test_case_insensitive_package_json_forbidden(self) -> None:
        self.assert_forbidden("PACKAGE.JSON", "forbidden dependency file")

    def test_lock_files_forbidden(self) -> None:
        for path in ["pnpm-lock.yaml", "packages/foo/yarn.lock", "bun.lockb"]:
            with self.subTest(path=path):
                self.assert_forbidden(path, "forbidden dependency file")

    def test_ci_paths_forbidden(self) -> None:
        for path in [
            ".github/workflows/deploy.yml",
            "apps/web/.github/workflows/deploy.yml",
            ".github\\workflows\\deploy.yml",
            ".circleci/config.yml",
            "packages/foo/.circleci/config.yml",
            ".buildkite/pipeline.yml",
            "services/api/.buildkite/pipeline.yml",
            "azure-pipelines.yml",
            "packages/foo/.gitlab-ci.yml",
            "Jenkinsfile",
            "apps/web/Jenkinsfile",
        ]:
            with self.subTest(path=path):
                self.assert_forbidden(path, "forbidden ci/cd file")

    def test_docker_paths_forbidden(self) -> None:
        self.assert_forbidden("apps/web/Dockerfile.prod", "forbidden docker file")

    def test_ci_substring_does_not_false_positive(self) -> None:
        for path in ["docs/decisions.yml", "src/scientific-config.yml", "src/circular.yml"]:
            with self.subTest(path=path):
                result = self.service.check_developer_write(
                    state=make_state(),
                    target_path=path,
                    operation="modify",
                    file_change_plan=plan(path),
                )
                self.assertTrue(result.allowed)

    def test_user_approved_forbidden_still_requires_risk_decision(self) -> None:
        result = self.service.check_developer_write(
            state=make_state(),
            target_path="package.json",
            operation="modify",
            file_change_plan=plan("package.json", owner="user-approved"),
        )

        self.assertFalse(result.allowed)
        self.assertEqual(result.failure_type, GateFailureType.RISK_DECISION_REQUIRED)
        self.assertIn("explicit_user_approved_forbidden_path", result.failed_conditions)


if __name__ == "__main__":
    unittest.main()
