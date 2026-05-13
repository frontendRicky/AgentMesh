# Python A2A Runtime V1 Release Checklist

## Required Checks

- [ ] Python 3.11+
- [ ] `compileall` pass
- [ ] `unittest` pass
- [ ] Smoke test pass
- [ ] E2E tests pass
- [ ] CLI JSON contract pass
- [ ] No `.ai-agents/**` protocol changes
- [ ] No `.cursor/**` changes
- [ ] No business source changes
- [ ] No dependency installation
- [ ] No real LLM call
- [ ] No git command execution
- [ ] No git tag, commit, or push executed
- [ ] No `package.json` / lock / CI/CD changes
- [ ] Final review Step 2 rejects missing or failed `test-report.md`
- [ ] P0/P1 risks cannot be bypassed by `mark_manual_required`
- [ ] `--project-root` rejects unsafe system roots
- [ ] Developer Gate rejects absolute paths, `..`, Windows separators, and monorepo package/lock/CI paths
- [ ] Prompt `[A2A]` header matches `.cursor/rules/ai-agents.mdc`
- [ ] Sensitive project-root prefixes are rejected
- [ ] Report archive symlinks are rejected
- [ ] `risk decide --by` local-user mismatch emits an audit warning
- [ ] Codex model hints never use unsupported `claude-*` commands
- [ ] Subprocess CLI smoke tests pass
- [ ] Monorepo CI paths under `.github`, `.circleci`, and `.buildkite` are blocked at any depth
- [ ] `P2_MEDIUM + requires_human_decision` unresolved risks block final-delivery

## Commands

```bash
PYTHONPYCACHEPREFIX=/private/tmp/a2a_runtime_pycache python3.11 -m compileall a2a_runtime tests
PYTHONPYCACHEPREFIX=/private/tmp/a2a_runtime_pycache python3.11 -m unittest discover -s tests
python3.11 -m a2a_runtime.cli --help
python3.11 -m a2a_runtime.cli --project-root . --json status
python3.11 -m a2a_runtime.cli --project-root . model recommend --agent developer --tool codex --json
```

## Release Candidate Metadata

- Version: `0.1.0rc5`
- Entry point: `a2a-agent = "a2a_runtime.cli:main"`
- Runtime invocation without install: `python3.11 -m a2a_runtime.cli`
- Git tag warning: do not execute `git tag`, `git commit`, or `git push` during RC validation. Tagging is a separate human release step after acceptance.

## Final Smoke Commands

```bash
python3.11 -m a2a_runtime.cli --project-root . --help
python3.11 -m a2a_runtime.cli --project-root . task list
python3.11 -m a2a_runtime.cli --project-root . task active
python3.11 -m a2a_runtime.cli --project-root . status
python3.11 -m a2a_runtime.cli --project-root . validate
python3.11 -m a2a_runtime.cli --project-root . prompt controller
python3.11 -m a2a_runtime.cli --project-root . report
```

## Human Sign-off

- [ ] Reviewer confirmed README and docs match current V1 behavior.
- [ ] Reviewer confirmed Runtime does not auto-run Cursor prompts.
- [ ] Reviewer confirmed Developer source writes remain outside Runtime and must pass GateService.
