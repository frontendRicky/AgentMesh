# Release Notes: Python A2A Runtime 0.1.0rc4

Version: `0.1.0rc4`

Protocol baseline: Markdown File-based A2A v1.0.0.

## Pilot Readiness

Opus second review allows Stage 0 / Stage 1 / Stage 2 real-project Pilot. Stage 3 / Stage 4 should remain under explicit human supervision.

## Fixed

- Sensitive project-root prefix rejection for `/etc/foo`, `/usr/local/foo`, `/private/tmp/foo`, `/System/foo`, `/Library/foo`, and similar paths.
- Symlink-safe report export: `archive/` and output parents must not be symlinks.
- `risk decide --by` local-user mismatch warning and RiskDecision payload audit fields.
- GateService injection in risk prompt regeneration.
- Removed GateService `current_agent` dead parameter.
- Codex model hints no longer emit `codex --model claude-*`.
- Low-cost model detection uses an allowlist.
- FinalDeliveryService normalizes RiskSeverity enum values.
- State history archive filenames use injected Clock.
- Scoped-id task extraction uses strict fullmatch patterns.
- Real subprocess CLI smoke tests.

## Safety

- No real LLM call.
- No Codex execution.
- No Cursor prompt execution.
- No git command execution.
- No automatic business source edits.
- No GateService bypass.
- No `.ai-agents` protocol changes.
- No `.cursor` changes.
