# Release Notes: Python A2A Runtime 0.1.0rc5

Version: `0.1.0rc5`

Protocol baseline: Markdown File-based A2A v1.0.0.

## Pilot Readiness

`0.1.0rc5` enables Stage 0 / Stage 1 / Stage 2 Pilot. Stage 3 / Stage 4 should remain under explicit human supervision.

## Fixed

- Monorepo CI path bypass in Developer Gate.
- `.github`, `.circleci`, and `.buildkite` are forbidden at any path depth.
- `.gitlab-ci.yml`, `azure-pipelines.yml`, `bitbucket-pipelines.yml`, `Jenkinsfile`, `Dockerfile`, `Dockerfile.*`, package files, and lock files remain forbidden at any path depth.
- No fuzzy `"ci"` substring matching is used.
- Subprocess CLI regression tests cover mutating and failure paths.
- `P2_MEDIUM + requires_human_decision == true + unresolved` blocks final-delivery.
- `P2_MEDIUM + requires_human_decision == false` does not block final-delivery.
- `P2_MEDIUM + requires_human_decision == true` with a legal RiskDecision can proceed and is referenced in final-delivery known risks.

## Safety

- No `.ai-agents` protocol changes.
- No `.cursor` changes.
- No business source modifications.
- No automatic business source edits.
- No real LLM calls.
- No Codex execution.
- No git command execution.
