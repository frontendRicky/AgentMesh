# Model Policy

Python A2A Runtime only recommends models. It does not call a real LLM, does not switch Cursor models, does not execute Codex, and does not run Cursor prompts automatically. The user must manually choose the model or manually run any displayed command hint.

## Per-Agent Model Recommendation

### Product Manager

- Role: `pm`
- Primary model: `claude-4.6-sonnet-medium-thinking`
- Fallback models: `gpt-5.5`, `claude-opus-4-7-thinking-high`
- Reasoning effort: medium
- Cost tier: medium
- Use cases: requirements clarification, scope boundaries, acceptance criteria, edge cases.
- Avoid for: P0/P1 risk final judgment and complex architecture tradeoffs.
- Rationale: PM work needs stable reasoning but usually not the highest-cost model.

### Architect

- Role: `architect`
- Primary model: `claude-opus-4-7-thinking-high`
- Fallback models: `gpt-5.5`, `claude-4.6-sonnet-medium-thinking`
- Reasoning effort: high
- Cost tier: high
- Use cases: design options, tradeoffs, impact analysis, risk identification, rollback planning.
- Avoid for: low-risk summaries and simple status explanations.
- Rationale: Architect work benefits from stronger long reasoning and risk judgment.

### Senior Frontend Developer

- Role: `developer`
- Primary model: `gpt-5.5`
- Codex model: `gpt-5.5`
- Fallback models: `claude-4.6-sonnet-medium-thinking`, `claude-opus-4-7-thinking-high`
- Reasoning effort: high
- Cost tier: high
- Use cases: implementation, complex refactor, multi-file edits, test repair.
- Avoid for: source edits that have not passed GateService.
- Rationale: Developer work in Codex scenarios is optimized for `gpt-5.5`.

### QA / Verifier

- Role: `qa`
- Primary model: `claude-opus-4-7-thinking-high`
- Fallback models: `gpt-5.5`, `claude-4.6-sonnet-medium-thinking`
- Reasoning effort: high
- Cost tier: high
- Use cases: acceptance checks, missed-case detection, regression risk, P0/P1 risk identification.
- Avoid for: low-risk formatting summaries.
- Rationale: QA should stay skeptical and use a high-reasoning model for high-risk verification.

### Flow Controller

- Role: `controller`
- Primary model: `gpt-5.5-mini`
- Fallback models: `gpt-5.5`
- Reasoning effort: low
- Cost tier: low
- Use cases: status explanation, report summaries, next-action hints, human-readable notes.
- Avoid for: P0/P1 risk decision work.
- Rationale: Controller decisions are mostly enforced by Python Runtime, so the default can be lower cost.

### Human Risk Decision Gate

- Role: `risk`
- Primary model: `claude-opus-4-7-thinking-high`
- Fallback models: `gpt-5.5`
- Reasoning effort: high
- Cost tier: high
- Use cases: risk grading, conflicting-option analysis, human option generation, P0/P1 review.
- Avoid for: lightweight status summaries.
- Rationale: P0/P1 risk work must not use a lightweight primary model.

## Cursor Usage

1. Run `python3.11 -m a2a_runtime.cli --project-root . prompt architect --tool cursor`.
2. Read the `Recommended Model` section.
3. Manually select the recommended model in the Cursor model picker.
4. Paste or run the generated prompt in Cursor.

Runtime will not switch Cursor models automatically.

## Codex Usage

1. Run `python3.11 -m a2a_runtime.cli --project-root . model recommend --agent developer --tool codex`.
2. Read the displayed command hint, for example `codex --model gpt-5.5`.
3. Manually run that command if you choose to use it.

Runtime will not execute Codex commands.

Codex command hints use OpenAI-compatible model names only. If the primary recommendation is a non-Codex model such as `claude-opus-4-7-thinking-high`, Runtime falls back to `gpt-5.5` for the Codex command hint and emits a warning. Controller + Codex + P0/P1 contexts also use `gpt-5.5` rather than a `claude-*` command.

## High-Risk Upgrade Strategy

P0/P1 risk contexts upgrade recommendations to high reasoning. Lightweight or mini models must not be primary for P0/P1 risk decision work. Runtime still does not decide risks for the user and does not accept risk automatically.

## Cost Control

- Controller defaults to a low-cost model.
- PM defaults to a medium-cost model.
- Architect, QA, and Risk default to high-reasoning models.
- Developer / Codex defaults to `gpt-5.5`.
- Large refactors and P0/P1 risk work should use high reasoning.

## V2 Roadmap

Potential future work:

- Real LLM provider integration.
- Configurable model policy files.
- Per-project model overrides.
- User-defined model routing.
- Automatic agent runtime routing.

V1 does not implement those capabilities.
