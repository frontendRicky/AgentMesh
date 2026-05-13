# Risk Decide By Handle

`risk decide --by <handle>` records who made a human risk decision. It is an audit field, not strong identity authentication.

Runtime reads the local user from `USER` or `getpass.getuser()`. If `--by` does not match the local user, the CLI does not reject the decision, but it emits a warning and writes the following fields into the RiskDecision payload:

- `decision_by`
- `local_user`
- `user_mismatch_warning`

Shared machines and delegated reviews need human discipline. Runtime does not authenticate the handle and does not prove that the named user made the decision.

