from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from a2a_runtime.core.frontmatter import load, loads
from a2a_runtime.core.errors import FrontmatterError


class FrontmatterCorruptInputsTests(unittest.TestCase):
    def test_corrupt_inputs_raise_clear_frontmatter_error(self) -> None:
        cases = {
            "missing_start": "schema_version: a2a/v1\n---\n",
            "missing_end": "---\nschema_version: a2a/v1\n",
            "tab_indent": "---\nschema_version: a2a/v1\nitems:\n\t- bad\n---\n",
            "duplicate_key": "---\nschema_version: a2a/v1\nname: one\nname: two\n---\n",
            "malformed_list": "---\nschema_version: a2a/v1\nitems: [one, two\n---\n",
            "malformed_mapping": "---\nschema_version: a2a/v1\nmeta: {a: 1\n---\n",
            "malformed_quote": "---\nschema_version: a2a/v1\nname: \"broken\n---\n",
            "root_list": "---\n- schema_version: a2a/v1\n---\n",
            "empty_key": "---\nschema_version: a2a/v1\n: value\n---\n",
            "no_colon": "---\nschema_version: a2a/v1\nbad line\n---\n",
            "bad_schema": "---\nschema_version: wrong\n---\n",
            "nested_object_error": "---\nschema_version: a2a/v1\nmeta: {a}\n---\n",
            "inline_depth_error": "---\nschema_version: a2a/v1\nitems: [one, {two: [bad}]\n---\n",
            "illegal_extra_indent": "---\nschema_version: a2a/v1\nname: ok\n  bad: indent\n---\n",
            "array_format_error": "---\nschema_version: a2a/v1\nitems: [bad]]\n---\n",
        }
        for name, text in cases.items():
            with self.subTest(name=name):
                with self.assertRaises(FrontmatterError):
                    loads(text)

    def test_edge_inputs_parse_or_fail_explicitly(self) -> None:
        valid_cases = {
            "empty_frontmatter_no_schema_required": ("---\n---\nbody\n", False),
            "crlf": ("---\r\nschema_version: a2a/v1\r\nname: ok\r\n---\r\nbody\r\n", True),
            "unicode": ("---\nschema_version: a2a/v1\nname: 设置页\n---\n正文\n", True),
            "colon_in_value": ("---\nschema_version: a2a/v1\nurl: http://example.test/a:b\n---\n", True),
            "single_quote": ("---\nschema_version: a2a/v1\nname: 'ok'\n---\n", True),
            "double_quote": ("---\nschema_version: a2a/v1\nname: \"ok\"\n---\n", True),
            "inline_array": ("---\nschema_version: a2a/v1\nitems: [one, two]\n---\n", True),
            "inline_mapping": ("---\nschema_version: a2a/v1\nmeta: {a: 1, b: two}\n---\n", True),
            "null": ("---\nschema_version: a2a/v1\nvalue: null\n---\n", True),
            "none_string": ("---\nschema_version: a2a/v1\nvalue: None\n---\n", True),
            "bool_upper": ("---\nschema_version: a2a/v1\nvalue: TRUE\n---\n", True),
            "body_missing": ("---\nschema_version: a2a/v1\n---\n", True),
            "body_contains_fence": ("---\nschema_version: a2a/v1\n---\nbody\n---\nmore\n", True),
            "yaml_comment": ("---\nschema_version: a2a/v1 # ok\nname: value # comment\n---\n", True),
            "multi_frontmatter_in_body": ("---\nschema_version: a2a/v1\n---\nbody\n---\nname: no\n---\n", True),
            "large_list": ("---\nschema_version: a2a/v1\nitems: [" + ", ".join(f"i{i}" for i in range(80)) + "]\n---\n", True),
        }
        for name, (text, require_schema) in valid_cases.items():
            with self.subTest(name=name):
                doc = loads(text, require_schema_version=require_schema)
                self.assertIsInstance(doc.data, dict)

    def test_non_utf8_file_raises_frontmatter_error(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.md"
            path.write_bytes(b"\xff\xfe\x00")

            with self.assertRaises(FrontmatterError):
                load(path)


if __name__ == "__main__":
    unittest.main()
