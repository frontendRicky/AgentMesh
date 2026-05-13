# Release Notes: Python A2A Runtime 0.1.0rc2

Version: `0.1.0rc2`

Protocol baseline: Markdown File-based A2A v1.0.0.

## Critical Fixes

- Final Review Step 2 now reads real QA artifacts and refuses `completed` when `test-report.md` is missing, failed, or blocked.
- P0 risk cannot use `approve_continue`, `accept_risk_and_continue`, or `mark_manual_required`.
- P1 `mark_manual_required` remains unresolved as `pending_manual_review` and blocks final delivery.
- CLI `--project-root` rejects sensitive roots and non-project roots unless explicitly allowed for tests.
- Developer Gate now normalizes target paths, rejects absolute paths and `..`, handles Windows separators, and blocks monorepo package/lock/CI/Docker paths without false-positive `ci` substring matching.
- GateService uses `state.current_agent`, not a caller-provided role.
- Prompt headers now match `.cursor/rules/ai-agents.mdc` exactly.
- Risk prompt regeneration uses GateService before allowing Developer write prompts.
- ReviewRecord validates reviewer identity at model construction and frontmatter parsing.
- Runtime write history is archived after the threshold instead of growing unbounded.

## Capabilities

- `task create`
- State machine
- Developer Gate
- Blocker two-stage flow
- Human Review double-step flow
- Final Delivery gate
- Human Risk Decision Gate
- Prompt generation
- CLI commands
- E2E sandbox tests

## Safety

- No business source modification.
- No real LLM call.
- No auto Cursor execution.
- No commit / push.
- No bypass review.
- No auto P0/P1 risk acceptance.

## Tests

- 317 tests OK during Phase 13 security validation.

## Limitations

- No LLM provider.
- No autonomous run.
- No HTTP server.
- No git integration.
- No automatic business source edits.
