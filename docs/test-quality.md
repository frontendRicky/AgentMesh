# Test Quality

The rc5 suite includes both in-process CLI tests and real subprocess smoke tests.

In-process tests call `a2a_runtime.cli.main()` directly and are useful for fast validation of result objects and JSON contracts.

Subprocess smoke tests call:

```bash
python3.11 -m a2a_runtime.cli ...
```

These tests verify module entry, argument parsing, stdout JSON, exit codes, and command wiring in a way closer to real usage. They use temporary project roots and do not call real LLMs, Codex, Cursor, git, or business source code writers.

Subprocess coverage includes happy paths plus mutating and failure-path regressions for `gate developer`, `risk decide`, `review approve --stage final --step 2`, and `finalize`.
