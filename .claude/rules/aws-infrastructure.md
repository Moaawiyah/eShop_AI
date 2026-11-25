---
paths:
  - "infrastructure/**"
  - "**/*.tf"
  - "**/*.tfvars*"
  - "**/*.hcl"
---

# AWS and Infrastructure Rules

Approval restrictions in CLAUDE.md section 12 always apply. PRD
references: section 15 (NFR-COST), FR-DEV-009, FR-DEV-010, FR-DEV-014.

## Allowed Without Approval
- Writing Terraform code, `terraform fmt`, `terraform validate` and static
  analysis that do not contact AWS.

## Requires Explicit Approval
- Any command that accesses an AWS account, including `terraform plan`
  against real accounts, `terraform apply` and `terraform destroy`.

## Cost Proposals
Before proposing any cloud resource, provide:
1. Purpose of each resource.
2. Estimated monthly cost (region stated; verify with the AWS Pricing
   Calculator).
3. Free or cheaper alternatives.
4. Removal procedure.
5. A request for approval.

AWS budget alerts are not spending caps.

## Cost-Aware Design
- Local first. Do not assume every technology must run in AWS.
- The container platform (ECS, EKS or EC2-based) is deferred until a cost
  evaluation and ADR.
- Justify high fixed-cost resources explicitly: NAT gateways, managed
  Kubernetes control planes, load balancers, multi-AZ databases, public
  IPv4 addresses and idle instances.
- Prefer the smallest suitable sizes, single-AZ for non-production, and
  ephemeral environments that can be destroyed when idle.
- Every environment has a documented teardown procedure.

## Terraform Practices
- Organize code into modules by concern; pin Terraform and provider
  versions; commit `.terraform.lock.hcl`.
- Store remote state encrypted with locking once cloud environments exist.
  Never commit state, plans or real `.tfvars` files (`*.tfvars.example`
  only).
- Tag all resources (`Project`, `Environment`, `ManagedBy`); never put
  personal information in tags.

## IAM and Secrets
- Least-privilege IAM; no root account usage; MFA required.
- CI uses GitHub OIDC roles scoped to the repository and branch.
- Use a managed secrets service (Secrets Manager or SSM Parameter Store,
  decided by ADR based on cost).
