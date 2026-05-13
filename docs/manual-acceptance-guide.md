# Manual Acceptance Guide

Use this guide to manually verify the Python A2A Runtime V1 Release Candidate in a sandbox project root. Do not run these commands against a real project until the sandbox pass is clean.

Do not execute `git tag`, `git commit`, or `git push` during manual acceptance. Release tagging is a separate human action after acceptance.

## 1. Check Version

```bash
python3.11 - <<'PY'
import a2a_runtime
print(a2a_runtime.__version__)
PY
```

Expected: `0.1.0rc5`.

## 2. Run Tests

```bash
PYTHONPYCACHEPREFIX=/private/tmp/a2a_runtime_pycache python3.11 -m compileall a2a_runtime tests
PYTHONPYCACHEPREFIX=/private/tmp/a2a_runtime_pycache python3.11 -m unittest discover -s tests
```

## 3. Create Sandbox Task

```bash
python3.11 -m a2a_runtime.cli --project-root /tmp/a2a-sandbox task create --type feature --title "Sandbox settings page" --priority P1 --owner zhangxia --yes
python3.11 -m a2a_runtime.cli --project-root /tmp/a2a-sandbox status
```

## 4. Generate Planning Prompts

```bash
python3.11 -m a2a_runtime.cli --project-root /tmp/a2a-sandbox prompt pm
python3.11 -m a2a_runtime.cli --project-root /tmp/a2a-sandbox prompt architect
```

The Runtime prints prompts only. It does not execute them.

## 5. Approve Architect Review

After the required Architect artifacts exist in the sandbox task workspace:

```bash
python3.11 -m a2a_runtime.cli --project-root /tmp/a2a-sandbox review approve --stage architect --step 1 --reviewer zhangxia --yes
python3.11 -m a2a_runtime.cli --project-root /tmp/a2a-sandbox review approve --stage architect --step 2 --reviewer zhangxia --yes
```

Confirm the task enters `developer_processing`.

## 6. Generate Developer Prompt and Gate Dry-run

```bash
python3.11 -m a2a_runtime.cli --project-root /tmp/a2a-sandbox prompt developer --path src/pages/settings/index.tsx --operation modify
python3.11 -m a2a_runtime.cli --project-root /tmp/a2a-sandbox gate developer --path src/pages/settings/index.tsx --operation modify
```

Developer source edits are still performed by Cursor, not by this Runtime, and remain constrained by GateService.

## 7. Blocker Flow

```bash
python3.11 -m a2a_runtime.cli --project-root /tmp/a2a-sandbox blocker request --from developer --reason "file-change-plan missing required file" --resume-to-agent architect --resume-to-status architect_processing --missing-artifact file_change_plan --required-fix "Add the missing file to file-change-plan" --yes
python3.11 -m a2a_runtime.cli --project-root /tmp/a2a-sandbox blocker create --from-request M-T-2026-001-001 --yes
python3.11 -m a2a_runtime.cli --project-root /tmp/a2a-sandbox blocker resolve B-T-2026-001-001 --missing-artifacts-resolved --yes
```

Use the actual message and blocker ids produced in your sandbox.

## 8. Risk Decision Flow

Create or inspect a risk review request message, then:

```bash
python3.11 -m a2a_runtime.cli --project-root /tmp/a2a-sandbox risk review RISK-T-2026-001-001
python3.11 -m a2a_runtime.cli --project-root /tmp/a2a-sandbox risk decide RISK-T-2026-001-001 --decision send_to_architect --reason "Need architecture replanning" --by zhangxia --yes
```

The Controller records the human decision and may generate a dispatch prompt. It does not choose or accept risk for the user.

## 9. Final Review and Finalize

After required PM, Architect, Developer, QA, and Human Review artifacts are present:

```bash
python3.11 -m a2a_runtime.cli --project-root /tmp/a2a-sandbox review approve --stage final --step 1 --reviewer zhangxia --yes
python3.11 -m a2a_runtime.cli --project-root /tmp/a2a-sandbox review approve --stage final --step 2 --reviewer zhangxia --yes
python3.11 -m a2a_runtime.cli --project-root /tmp/a2a-sandbox finalize --yes
```

Finalize must fail if unresolved P0/P1 risks or active blockers remain.

## 10. Report Export

```bash
python3.11 -m a2a_runtime.cli --project-root /tmp/a2a-sandbox report
python3.11 -m a2a_runtime.cli --project-root /tmp/a2a-sandbox report --output archive/runtime-report.md --yes
```

Report export writes only inside the current task archive.

## 11. Safety Confirmation

- Confirm no business source files changed unless Cursor made those edits separately.
- Confirm `.ai-agents` protocol files were not modified.
- Confirm `.cursor` was not modified.
- Confirm no git command, commit, push, or MR creation happened.
- Confirm no real LLM API was called.
- Confirm no Cursor prompt was automatically executed by the Runtime.
- Confirm GateService was not bypassed for Developer source edits.
