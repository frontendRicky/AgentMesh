# CHANGELOG

## 0.1.0rc5 — Pilot Safety Fixes

### Fixed

- Developer Gate now treats `.github`, `.circleci`, and `.buildkite` as forbidden CI/CD directories at any monorepo depth.
- Developer Gate still avoids fuzzy `"ci"` substring matching, so `docs/decisions.yml`, `src/scientific-config.yml`, and `src/circular.yml` are not false positives.
- Final Delivery now blocks unresolved `P2_MEDIUM` risks when `requires_human_decision == true`.
- Final Delivery allows `P2_MEDIUM` risks without human-decision requirement, while keeping them visible in risk/report data.
- Subprocess CLI tests now cover mutating and failure paths for gate, risk decide, review final step2, and finalize blocking risk behavior.

### Pilot

- Stage 0 / Stage 1 / Stage 2 Pilot can proceed on `0.1.0rc5`.
- Stage 3 / Stage 4 remain supervised.

## 0.1.0rc4 — Safety Fixes + Pilot Readiness

### Fixed

- Reject sensitive `--project-root` prefixes such as `/etc/foo`, `/usr/local/foo`, and `/private/tmp/foo`.
- Reject report exports when `archive/` or any output parent is a symlink.
- Add local-user audit warning for `risk decide --by` mismatches.
- Persist `local_user` and `user_mismatch_warning` in RiskDecision message payloads.
- Inject GateService into RiskPromptRegenerationService instead of constructing an internal temporary service.
- Remove the misleading `current_agent` parameter from GateService; state remains the source of truth.
- Prevent Codex command hints from using unsupported `claude-*` model names.
- Replace fuzzy lightweight-model substring checks with an explicit low-cost model allowlist.
- Use RiskSeverity enum normalization in FinalDeliveryService blocking checks.
- Use injected Clock for StateRepo history archive file names.
- Use strict scoped-id fullmatch parsing for task id extraction.
- Add subprocess CLI smoke coverage.

### Safety

- Stage 0 / Stage 1 / Stage 2 real-project Pilot can proceed.
- Stage 3 / Stage 4 should remain under human supervision.
- Runtime still does not call real LLM, execute Codex, execute Cursor prompts, run git, or modify business source code.

## 0.1.0rc3 — Model Policy + Agent Model Routing

### Added

- `ModelPolicy` / `AgentModelPreference` / `ModelSelectionResult` data models.
- `ModelSelectionService` with per-agent default model recommendations.
- `model` CLI command for listing policy and rendering recommendations.
- `Recommended Model` section in generated Agent prompts.
- `Recommended Model` section in risk regeneration prompts.
- Codex command hint generation such as `codex --model gpt-5.5`.
- Cursor manual model selection instruction.
- `docs/model-policy.md`.

### Safety

- Runtime does not call real LLM.
- Runtime does not auto-switch Cursor model.
- Runtime does not execute Codex command.
- Runtime does not auto-run prompts.
- Model routing is advisory only and does not change GateService, Human Review, Blocker, Risk Decision, or Final Delivery rules.

## 0.1.0rc2 — Python A2A Runtime V1 Release Candidate

### Critical Fixes

- Final Review Step 2 no longer trusts caller-provided `test_report_clean`; it reads QA artifacts.
- P0/P1 risk cannot be bypassed with `mark_manual_required`.
- CLI `--project-root` now rejects unsafe system roots and non-project roots by default.
- Developer Gate now normalizes paths and blocks monorepo package/lock/CI/Docker targets.
- Prompt `[A2A]` headers now match the Cursor A2A rule.
- Risk prompt regeneration now delegates Developer write permission to GateService.
- Review records validate reviewer identity at model construction.
- Runtime write history now archives after threshold.

### Added

- Markdown A2A v1.0.0 protocol execution.
- Task / State / Message / Artifact / Blocker / Review models.
- State Machine.
- Developer Gate.
- `gate_failure` / `blocker_request`.
- Formal Blocker two-stage flow.
- Human Review / Final Review double-step flow.
- Final Delivery gate.
- Human Risk Decision Gate.
- Risk Prompt Regeneration.
- Agent Profile merge.
- Cursor Prompt generation.
- CLI read-only commands.
- CLI mutating commands with `--dry-run` / `--yes`.
- E2E sandbox test suite.
- CLI help / error / JSON contract hardening.
- Report export to task archive.

### Safety

- Does not modify business source code.
- Does not call real LLM.
- Does not auto-run Cursor prompts.
- Does not commit or push.
- Does not modify `.ai-agents` protocol files.
- Does not bypass human review.
- Does not accept P0/P1 risk automatically.

### Tests

- 244+ tests passing.
- 251 tests OK during Release Candidate documentation pass.
- 317 tests OK during Phase 13 security validation.

### Release Notes

- See `docs/release-notes-0.1.0rc2.md`.
- Release Candidate validation must not execute `git tag`, `git commit`, or `git push`.
