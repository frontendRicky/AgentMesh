# Known Limitations

Python A2A Runtime `0.1.0rc5` is a local Markdown file runtime and release candidate. It intentionally avoids autonomous execution.

## Not Implemented

- No LLM provider.
- No real LLM calls.
- No autonomous run.
- No `run pm`.
- No `run architect`.
- No `run developer`.
- No `run qa`.
- No HTTP server.
- No git integration.
- No git tag, commit, push, or MR creation.
- No automatic Cursor prompt execution.
- No automatic business source edits.
- No full RiskScannerService.
- No strong identity authentication for `risk decide --by`; it is an audit handle only.

## Operational Limits

- The Runtime depends on existing Markdown A2A conventions and task workspace files.
- Cursor remains responsible for actual agent work and business source edits.
- Developer source edits must be validated with GateService before execution in Cursor.
- Risk scanning is explicit and message-based in V1; it is not a full repository scanner.
- Report export is restricted to the current task archive.
- Report export rejects symlinked archive paths.

## Safety Limits

- The Runtime will not accept P0/P1 risk automatically.
- The Runtime will not bypass Human Review.
- The Runtime will not bypass GateService.
- The Runtime will not bypass the two-stage Blocker flow.
- The Runtime will not bypass FinalDeliveryService gates.
