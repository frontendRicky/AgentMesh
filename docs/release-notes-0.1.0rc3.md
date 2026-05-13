# Release Notes: Python A2A Runtime 0.1.0rc3

Version: `0.1.0rc3`

Protocol baseline: Markdown File-based A2A v1.0.0.

## Added

- ModelPolicy, AgentModelPreference, and ModelSelectionResult models.
- ModelSelectionService for per-agent model recommendation.
- `model list`, `model policy`, and `model recommend` CLI commands.
- Recommended Model section in generated Agent prompts.
- Recommended Model section in risk regeneration prompts.
- Cursor manual model selection instruction.
- Codex command hint generation, for example `codex --model gpt-5.5`.
- Documentation in `docs/model-policy.md`.

## Safety

- No real LLM call.
- No automatic Cursor model switching.
- No automatic Codex command execution.
- No automatic Cursor prompt execution.
- No automatic business source edits.
- No GateService bypass.
- No Human Review bypass.
- No automatic P0/P1 risk acceptance.

## Default Recommendations

- PM: `claude-4.6-sonnet-medium-thinking`.
- Architect: `claude-opus-4-7-thinking-high`.
- Developer / Codex: `gpt-5.5`.
- QA / Verifier: `claude-opus-4-7-thinking-high`.
- Controller: `gpt-5.5-mini`, upgraded for P0/P1 contexts.
- Human Risk Decision Gate: `claude-opus-4-7-thinking-high`.

## Limitations

- No LLM provider.
- No autonomous run.
- No HTTP server.
- No git integration.
- No automatic business source edits.
- Model routing is recommendation-only.
