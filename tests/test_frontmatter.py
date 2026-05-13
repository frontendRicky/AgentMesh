import unittest

from a2a_runtime.core import frontmatter
from a2a_runtime.core.errors import FrontmatterError


class FrontmatterTests(unittest.TestCase):
    def test_parse_nested_frontmatter_and_body(self) -> None:
        document = frontmatter.loads(
            """---
task_id: T-2026-001
required_response: true
payload:
  message: hello
  values: [one, two]
scope:
  in_scope:
    - build runtime
  out_of_scope:
    - call llm
schema_version: a2a/v1
---

# Body
"""
        )

        self.assertEqual(document.data["task_id"], "T-2026-001")
        self.assertTrue(document.data["required_response"])
        self.assertEqual(document.data["payload"]["values"], ["one", "two"])
        self.assertEqual(document.data["scope"]["out_of_scope"], ["call llm"])
        self.assertEqual(document.body, "# Body\n")

    def test_dump_round_trips_minimal_supported_yaml(self) -> None:
        dumped = frontmatter.dumps(
            {
                "task_id": "T-2026-001",
                "items": ["a", "b"],
                "nested": {"enabled": True, "count": 2, "nothing": None},
                "schema_version": "a2a/v1",
            },
            "hello",
        )
        parsed = frontmatter.loads(dumped)

        self.assertEqual(parsed.data["items"], ["a", "b"])
        self.assertEqual(parsed.data["nested"]["enabled"], True)
        self.assertEqual(parsed.data["nested"]["count"], 2)
        self.assertIsNone(parsed.data["nested"]["nothing"])
        self.assertEqual(parsed.body, "hello\n")

    def test_requires_schema_version(self) -> None:
        with self.assertRaises(FrontmatterError):
            frontmatter.loads(
                """---
task_id: T-2026-001
---
"""
            )


if __name__ == "__main__":
    unittest.main()
