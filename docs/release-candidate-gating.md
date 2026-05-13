# Release Candidate Gating

Python A2A Runtime `0.1.0rc5` is the minimum Release Candidate after the Phase 13 P0/P1 fixes, Phase 15 Pilot safety fixes, and Phase 16 monorepo CI/P2 policy fixes.

Do not pilot `0.1.0rc1` in a real project unless the Phase 13 fixes are applied.

## Required Gates

- Review approve must use explicit `--step 1` or `--step 2`.
- Final Review Step 2 must read `artifacts/qa/test-report.md` and `artifacts/qa/acceptance-checklist.md`.
- P0/P1 risks must remain blocking unless a legal human decision resolves them.
- `mark_manual_required` must not silently accept P0/P1 risk.
- Developer writes must pass GateService with normalized project-relative paths.
- Prompt headers must match `.cursor/rules/ai-agents.mdc`.
- Sensitive project-root prefixes must be rejected.
- Report archive symlinks must be rejected.
- Codex command hints must not use unsupported `claude-*` model commands.
- `risk decide --by` is audit-only and mismatch warnings must be preserved.
- Developer Gate must block `.github`, `.circleci`, and `.buildkite` at any monorepo depth.
- `P2_MEDIUM + requires_human_decision` unresolved risks must block final-delivery.

## Release Candidate Commands

```bash
PYTHONPYCACHEPREFIX=/private/tmp/a2a_runtime_pycache python3.11 -m compileall a2a_runtime tests
PYTHONPYCACHEPREFIX=/private/tmp/a2a_runtime_pycache python3.11 -m unittest discover -s tests
python3.11 -m a2a_runtime.cli --help
```

Do not execute `git tag`, `git commit`, or `git push` as part of Runtime validation.
