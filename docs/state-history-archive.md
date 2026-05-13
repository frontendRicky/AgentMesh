# State History Archive

State write history is appended to `state.md` without changing the frozen frontmatter schema.

When runtime write history grows past the threshold, `StateRepo` keeps the most recent entries in `state.md` and archives older rows under:

```txt
workspace/<task-id>/archive/state-history-<timestamp>.md
```

As of rc4, archive filenames use the injected `Clock`, which makes tests stable and lets future callers control timestamps.

