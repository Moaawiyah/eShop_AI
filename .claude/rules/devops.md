---
paths:
  - "deployment/**"
  - "monitoring/**"
  - "scripts/**"
  - ".github/**"
  - "**/Dockerfile*"
  - "**/docker-compose*.yml"
  - "**/compose*.yaml"
---

# DevOps Rules

PRD references: section 12 (FR-DEV). Roadmap: M1, M7, M8, M10.

## Containers
- Multi-stage builds, minimal pinned base images, non-root user,
  health checks and a `.dockerignore`.
- Never bake secrets into images or layers.
- Docker Compose is for local development; bind ports to localhost and
  read configuration from `.env`.

## CI/CD (GitHub Actions)
- Declare least-privilege `permissions:` in every workflow.
- Pin third-party actions to a full commit SHA.
- Never print secrets; use OIDC for cloud access, never long-lived keys.
- Use caching and path filters to stay within free CI capacity.
- CI never runs `terraform apply`, destroys resources or deploys to the
  cloud without a manual approval gate and explicit user approval.
- Basic scanning from M1 (Gitleaks, Dependabot, pip-audit, npm audit);
  Trivy image and IaC scanning and blocking thresholds from M7.

## Kubernetes and GitOps
- Use kind for local Kubernetes.
- Helm charts live in `deployment/helm/`; lint and template them in CI.
- Workloads define resource requests and limits, liveness and readiness
  probes, non-root execution and read-only root filesystems where practical.
- Never commit plaintext secrets to Git.
- Argo CD deploys from Git; no manual changes to managed clusters.
- Use immutable image tags (Git commit SHA) promoted across environments.

## Observability
- Structured JSON logs with correlation IDs, OpenTelemetry traces and
  Prometheus metrics.
- Dashboards and alert rules are stored as code in `monitoring/`.

## Releases and Rollback
- Maintain a documented, rehearsed rollback procedure.
- Database migrations follow expand/contract.

## Scripts
- Scripts are idempotent, use `set -euo pipefail`, contain no personal
  paths and ask for confirmation before destructive actions.
