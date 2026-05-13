# Python A2A Runtime

Status: V1 Release Candidate — 0.1.0rc5

This runtime executes Markdown File-based A2A v1.0.0.
It does not modify business source code and does not call real LLM APIs.

## Quick Start

```bash
python3.11 -m a2a_runtime.cli --project-root . task create --type feature --title "新增设置页" --priority P1 --owner zhangxia --yes
python3.11 -m a2a_runtime.cli --project-root . status
python3.11 -m a2a_runtime.cli --project-root . prompt pm
python3.11 -m a2a_runtime.cli --project-root . prompt architect
python3.11 -m a2a_runtime.cli --project-root . review approve --stage architect --step 1 --reviewer zhangxia --yes
python3.11 -m a2a_runtime.cli --project-root . review approve --stage architect --step 2 --reviewer zhangxia --yes
python3.11 -m a2a_runtime.cli --project-root . prompt developer --path src/pages/settings/index.tsx --operation modify
python3.11 -m a2a_runtime.cli --project-root . gate developer --path src/pages/settings/index.tsx --operation modify
python3.11 -m a2a_runtime.cli --project-root . report
```

## Commands

- `status`, `validate`, `task list`, `task active`, `prompt`, `gate developer`, `risk list/show/review/prompt`, and `report` are read-only.
- `task create`, `task use`, `review approve/reject`, `blocker request/create/resolve`, `risk decide`, `finalize`, and `report --output archive/...` can write workspace files.
- Mutating commands require `--yes` for actual writes and support `--dry-run` where applicable.
- All commands support `--project-root`; JSON output is available with `--json`.
- `model list`, `model policy`, and `model recommend` show per-agent model recommendations only; they do not call or switch models.

## Model Policy

Runtime can recommend a model for each Agent, but it does not call LLM APIs and does not switch Cursor models automatically.

- PM defaults to a medium reasoning model for requirements and acceptance criteria.
- Architect, QA / Verifier, and Human Risk Decision Gate default to high reasoning models.
- Developer / Codex scenarios default to `gpt-5.5`.
- Flow Controller defaults to a lower-cost model, then upgrades recommendations for P0/P1 risk contexts.
- Cursor prompts include a manual model-selection instruction.
- Codex prompts and `model recommend --tool codex` include a copyable `codex --model ...` command hint, but Runtime never executes it.

## What Runtime Does

- Executes the Markdown A2A v1.0.0 task protocol locally.
- Manages task, state, message, artifact, blocker, review, risk, and final-delivery files.
- Generates Cursor prompts for PM, Architect, Developer, QA, Controller, and risk dispatches.
- Checks Developer Gate against state and file-change-plan.
- Handles Human Review, two-stage Blocker, Human Risk Decision Gate, and FinalDeliveryService gates.

## What Runtime Does NOT Do

- Does not modify business source code.
- Does not call a real LLM.
- Does not auto-run Cursor prompts.
- Does not commit or push.
- Does not modify `.ai-agents` protocol files.
- Does not modify `.cursor` rules.
- Does not bypass human review, risk decisions, blocker flow, or final-delivery gates.

## Safety Model

- `task.md` stores static task fields only.
- `state.md` is the only dynamic state source and is written by controller flows only.
- Developer writes are controlled by GateService and file-change-plan.
- Blockers use a two-stage flow: professional request, Controller formal blocker.
- Human Review uses double-step transitions.
- P0/P1 risks require explicit human decisions before progress.
- Final delivery requires final review, clean QA evidence, no active blocker, and no unresolved blocking risk.
- Mutating CLI commands require `--yes`; `--dry-run` previews planned writes.
- `--project-root` must resolve to a safe project root with `.ai-agents/`, `.git/`, `pyproject.toml`, or `package.json`.

## Real Project Onboarding

1. Confirm Python 3.11+ and a project-local `.ai-agents/**` tree.
2. Start with read-only checks:

```bash
python3.11 -m a2a_runtime.cli --project-root . status
python3.11 -m a2a_runtime.cli --project-root . validate
python3.11 -m a2a_runtime.cli --project-root . task list
```

3. Create a task only after confirming the project root:

```bash
python3.11 -m a2a_runtime.cli --project-root . task create --type feature --title "xxx" --priority P1 --owner <you> --yes
python3.11 -m a2a_runtime.cli --project-root . prompt pm
```

4. Use Runtime prompts with Cursor manually: Runtime prints prompts, the user reviews them, Cursor performs the agent work, and Runtime validates state, gates, reviews, blockers, risks, and final delivery.

See `docs/real-project-onboarding.md` for the longer guide.

Pilot readiness note:

- `0.1.0rc5` is suitable for Stage 0 / Stage 1 / Stage 2 real-project Pilot.
- Stage 3 / Stage 4 should remain under explicit human supervision.
- `risk decide --by` is an audit handle, not strong identity authentication. Runtime records local-user mismatch warnings when possible.
- Report export refuses symlinked archive paths and stays inside the current task archive.

## What V1 Does

- Executes Markdown A2A v1.0.0 task flow.
- Manages task/state/message/artifact/blocker/review/risk/final-delivery files.
- Generates PM, Architect, Developer, QA, Controller, and risk dispatch prompts.
- Enforces Developer Gate, Human Review, Blocker, Human Risk Decision, and Final Delivery gates.
- Provides safe CLI commands, JSON contracts, report export, sandbox E2E tests, and release readiness docs.

## What V1 Does Not Do

- Does not implement a real LLM provider.
- Does not call real LLM APIs.
- Does not implement full autonomous run.
- Does not implement `run pm`, `run architect`, `run developer`, or `run qa`.
- Does not automatically execute Cursor Prompt.
- Does not automatically modify business source code.
- Does not commit, push, or create MR.
- Does not modify `.ai-agents` protocol structure.
- Does not modify `.cursor`.

## Phase History

- Phase 1 Core File Runtime: path helpers, frontmatter parsing/dumping, ID checks, clock, constants, errors, and the first repositories.
- Phase 2 Models + Validation: dataclass/Enum models and validation entry points for task, state, message, artifact, blocker, review, agent card, handoff, file change audit, changed files, risk, and risk decision records.
- Phase 3 State Machine + Flow Controller Skeleton: the 14-status transition table, review double-step helpers, F-08 startup recovery checks, basic blocked recovery, runtime write-history append helpers, MessageRepo, ArtifactRepo, and a minimal FlowControllerAgent facade.
- Phase 4 Gate + Blocker: Developer Gate checks, `gate_failure` message creation, professional-agent `blocker_request` messages, Controller-only formal Blocker creation, blocked state writes, and basic Blocker resolve.
- Phase 5 Review + Final Delivery: ReviewRepo, ReviewService, FinalDeliveryService, Architect/Final Review record creation, approved/rejected review flows, final-delivery gate validation, and final-delivery writing.
- Phase 6 Human Risk Decision Gate: runtime risk findings, message-based risk review requests, human risk decisions, risk decision dispatch, minimal Cursor prompt regeneration, unresolved P0/P1 final-delivery blocking, and FlowControllerAgent risk facade methods.
- Phase 7 Agent Profile + Prompt Generation: AgentProfile fusion, read-only profile/reference repositories, PromptService for PM/Architect/Developer/QA/Controller prompts, shared A2A prompt sections, Developer GateService prompt checks, and prompt overreach protections.
- Phase 8A Minimal Safe CLI: argparse-based `python -m a2a_runtime.cli` entry, safe status/validate/prompt/task/risk/gate commands, JSON output, explicit exit codes, and dry-run Developer Gate checks.
- Phase 8B Mutating CLI Commands: controlled `task create`, `review approve/reject`, `blocker request/create/resolve`, `risk decide`, `finalize`, and read-only `report` commands with `--dry-run`/`--yes` write protection.
- Phase 9 End-to-End Test Suite: sandbox E2E fixtures, lifecycle/review/gate/blocker/risk/finalize/report coverage, JSON contract tests, and safety boundary regression.
- Phase 10 Runtime Hardening + CLI Polish: help text, structured errors, JSON hardening, report export, smoke tests, and V1 release checklist.
- Phase 11 Release Candidate: version `0.1.0rc1`, CHANGELOG, release docs, manual acceptance guide, onboarding guide, smoke command docs, and safety boundary docs.
- Phase 12 Release Tag Prep: release notes, pilot checklist, clean-environment validation, final safety checklist, and known limitations.
- Phase 13 Critical Security + Protocol Fixes: version `0.1.0rc2`, Final Review test-report enforcement, P0/P1 risk blocking fixes, safe project-root validation, strict Developer Gate path normalization, strict A2A prompt header, reviewer model validation, and state-history archive.
- Phase 14 Model Policy + Agent Model Routing: version `0.1.0rc3`, default model recommendations per Agent, model CLI commands, Recommended Model prompt sections, Cursor manual-selection guidance, and Codex command hints without model execution.
- Phase 15 Safety Fixes + Pilot Readiness: version `0.1.0rc4`, sensitive project-root prefix rejection, symlink-safe report export, risk decision local-user audit warnings, GateService injection cleanup, Codex-safe model hints, stable state-history archive clocks, strict scoped-id parsing, and subprocess CLI smoke tests.
- Phase 16 Pilot Safety Fixes: version `0.1.0rc5`, monorepo CI path blocking in Developer Gate, subprocess mutating/failure CLI regression coverage, and explicit P2_MEDIUM final-delivery policy.

Out of scope for this round:

- Full run commands (`run pm`, `run architect`, `run developer`, `run qa`, or full autonomous workflow execution).
- Full RiskScannerService.
- LLM providers or any real LLM invocation.
- Any automatic writes to business source code.
- Any changes to `.ai-agents` protocol files or `.cursor`.

Risk gate note:

- Phase 6 keeps risk persistence compatible with the frozen Markdown protocol by writing `risk_review_request`, `risk_decision`, and `risk_decision_dispatch` messages under the task message bus.
- Controller never selects or accepts a risk decision. Human decisions must be recorded as `from-human-*-risk-decision.md`, and P0/P1 risks remain blocking until an explicit valid human decision exists.
- Risk prompts are generated as text-only dispatch messages. They do not execute, call an LLM, or modify PM/Architect/Developer/QA artifacts or business source files.

Profile and prompt note:

- Phase 7 reads `.ai-agents` and `.cursor/rules/ai-agents.mdc` as immutable references. It does not write protocol files or Cursor rules.
- A2A hard rules have priority over Agent Cards, Handoff Contracts, flows, colleague persona files, and template defaults. Conflicts involving write permissions, review, blocker, risk, state, or final delivery are recorded in the profile conflict matrix.
- PromptService emits text prompts only. PM, Architect, QA, and Controller prompts always say `May Write Code: no`; Developer prompts call GateService and only say `yes` when the current state, human review status, file-change-plan whitelist, and forbidden-path rules all pass.
- PromptService also emits a `Recommended Model` section after the strict `[A2A]` header. This section is advisory only and never changes `May Write Code` behavior.

CLI note:

- The CLI is available without installation through `python3.11 -m a2a_runtime.cli`; `pyproject.toml` also reserves the `a2a-agent` script name for installed usage.
- Every implemented command accepts `--project-root`, `--task-id`, `--json`, and `--verbose`. `--project-root` defaults to the current directory, and task resolution prefers explicit `--task-id`, then `active-task.md`, then a single task directory.
- Read-only commands remain read-only: status, validate, prompt, gate developer, risk list/show/review/prompt, task list/active, and report.
- Model commands are read-only: `model list`, `model policy`, and `model recommend`.
- Mutating commands require `--yes` to write or `--dry-run` to preview. They go through service-layer APIs instead of hand-writing runtime files in CLI code.
- `task create` initializes only the task workspace, `task.md`, `state.md`, directories, the first controller handoff message, and optionally `active-task.md`.
- `review approve/reject` records human review proxy actions from a real reviewer handle, then uses ReviewService for double-step state transitions.
- `blocker request/create/resolve` preserves the two-stage blocker model: professional agents create request messages; Controller creates formal blockers and resolves them.
- `risk decide` records a `from-human-*-risk-decision.md` message and dispatches text prompts when regeneration is required; it does not execute prompts or modify business code.
- `finalize` writes `artifacts/final/final-delivery.md` only after FinalDeliveryService gates pass, including no unresolved P0/P1 risks.
- `report` prints to stdout by default. `report --output archive/runtime-report.md --yes` exports only inside the current task archive; `--dry-run` previews that write.
- Text errors use a consistent `[A2A CLI Error]` shape. JSON errors include `code`, `message`, and `suggested_next_action`.

End-to-End Testing:

- Phase 9 adds sandbox end-to-end coverage for task lifecycle, human review, Developer Gate, Blocker two-stage flow, Human Risk Decision Gate, final delivery, report output, JSON contracts, and safety boundaries.
- E2E tests use `tempfile.TemporaryDirectory()` project roots only. They do not write the real `.ai-agents/workspace`, do not write business source directories, do not call LLMs, and do not depend on a git repository.
- Run the full suite with:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/a2a_runtime_pycache python3.11 -m compileall a2a_runtime tests
PYTHONPYCACHEPREFIX=/private/tmp/a2a_runtime_pycache python3.11 -m unittest discover -s tests
```

Minimal manual flow:

```bash
python3.11 -m a2a_runtime.cli --project-root . task create --type feature --title "新增设置页" --priority P1 --owner zhangxia --yes
python3.11 -m a2a_runtime.cli --project-root . status
python3.11 -m a2a_runtime.cli --project-root . prompt pm
python3.11 -m a2a_runtime.cli --project-root . prompt architect
python3.11 -m a2a_runtime.cli --project-root . review approve --stage architect --step 1 --reviewer zhangxia --yes
python3.11 -m a2a_runtime.cli --project-root . review approve --stage architect --step 2 --reviewer zhangxia --yes
python3.11 -m a2a_runtime.cli --project-root . prompt developer --path src/pages/settings/index.tsx --operation modify
python3.11 -m a2a_runtime.cli --project-root . gate developer --path src/pages/settings/index.tsx --operation modify
python3.11 -m a2a_runtime.cli --project-root . report
```

This Runtime does not automatically execute prompts, does not automatically modify business source, and does not call an LLM. Actual source edits still happen in Cursor and remain constrained by GateService.

## Release Checklist

- `compileall` pass.
- `unittest` pass.
- Smoke test pass.
- E2E tests pass.
- CLI JSON contract pass.
- No `.ai-agents/**` protocol changes.
- No `.cursor/**` changes.
- No business source changes.
- No dependencies installed.
- No real LLM call.
- No full autonomous run command.
- No `run pm`, `run architect`, `run developer`, or `run qa` command.
- No unresolved P0/P1 risk can finalize.

State history note:

- Runtime transitions return a `StateTransitionResult`; `StateRepo.write_with_history` appends a `## Runtime Write History` table to the Markdown body without changing the frozen frontmatter schema.
- When runtime history exceeds the threshold, older entries are archived under `workspace/<task-id>/archive/state-history-*.md` and the current file stays compact.

Run tests with:

```bash
python3.11 -m unittest discover -s tests
```

The project uses only the Python standard library and requires Python 3.11 or newer.

## Next Roadmap

- Prepare V1 release tag and signed release notes.
- Add sample sandbox workspace fixture for docs only.
- Add optional packaging verification in a clean virtual environment.
- Keep LLM provider, autonomous run commands, and business source editing outside V1.

## Release Candidate Docs

- Release notes: `docs/release-notes-0.1.0rc5.md`
- Model policy: `docs/model-policy.md`
- Pilot stage checklist: `docs/pilot-stage-checklist.md`
- Symlink policy: `docs/symlink-policy.md`
- Risk decision matrix: `docs/risk-decision-matrix.md`
- Forbidden paths: `docs/forbidden-paths.md`
- Release checklist: `docs/release-checklist.md`
- Manual acceptance guide: `docs/manual-acceptance-guide.md`
- Real project onboarding: `docs/real-project-onboarding.md`
- Real project pilot checklist: `docs/real-project-pilot-checklist.md`
- Clean environment validation: `docs/clean-environment-validation.md`
- Smoke commands: `docs/smoke-commands.md`
- Safety boundaries: `docs/safety-boundaries.md`
- Known limitations: `docs/known-limitations.md`
- Release candidate gating: `docs/release-candidate-gating.md`
- Project root safety: `docs/project-root-safety.md`
- File-change-plan authoring: `docs/file-change-plan-authoring.md`
- CLI exit codes: `docs/cli-exit-codes.md`

Do not execute `git tag`, `git commit`, or `git push` during Release Candidate validation. Tag preparation is allowed as documentation only; creating the actual tag is a separate human release action.
