# Forbidden Paths

Developer Gate treats the following paths as forbidden by default. A forbidden path cannot produce `May Write Code: yes`; it must go through Human Risk Decision handling.

## Dependency Files

Any basename matching:

- `package.json`
- `package-lock.json`
- `pnpm-lock.yaml`
- `yarn.lock`
- `bun.lock`
- `bun.lockb`

## CI/CD

Any path segment matching:

- `.github`
- `.circleci`
- `.buildkite`

Any basename matching:

- `.gitlab-ci.yml`
- `azure-pipelines.yml`
- `bitbucket-pipelines.yml`
- `Jenkinsfile`

This applies inside monorepos. For example:

- `.github/workflows/deploy.yml`
- `apps/web/.github/workflows/deploy.yml`
- `packages/foo/.circleci/config.yml`
- `services/api/.buildkite/pipeline.yml`

## Docker

Any basename matching:

- `Dockerfile`
- `Dockerfile.*`

## False Positive Guard

Developer Gate must not use fuzzy `"ci"` substring matching. These paths are not forbidden just because they contain similar letters:

- `docs/decisions.yml`
- `src/scientific-config.yml`
- `src/circular.yml`
