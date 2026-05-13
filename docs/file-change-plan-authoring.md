# File Change Plan Authoring

Developer source edits are allowed only when GateService passes.

Every entry should be project-relative and must not use absolute paths, `..`, or Windows drive prefixes.

## Required Entry Fields

- `path`
- `operation`: `create`, `modify`, or `delete`
- `allowed`
- `reason`
- `risk`
- `owner`

## Forbidden Paths

GateService treats these as forbidden at any directory depth and case-insensitively where relevant:

- `package.json`
- `package-lock.json`
- `pnpm-lock.yaml`
- `yarn.lock`
- `bun.lock`
- `bun.lockb`
- `.github/**`
- `.gitlab-ci.yml`
- `.circleci/**`
- `.buildkite/**`
- `azure-pipelines.yml`
- `bitbucket-pipelines.yml`
- `Jenkinsfile`
- `Dockerfile`
- `Dockerfile.*`

For monorepos, `.github`, `.circleci`, and `.buildkite` are forbidden at any path segment, not only at repository root. See `docs/forbidden-paths.md`.

Even when such a path is marked `allowed: yes` and `owner: user-approved`, Runtime returns `risk_decision_required`; it does not silently allow the write.

Do not use broad `ci` substring matching. Files such as `docs/decisions.yml`, `src/scientific-config.yml`, and `src/circular.yml` are not CI/CD by name alone.
