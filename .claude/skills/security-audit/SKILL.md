---
name: security-audit
description: "Audit eShop_AI security controls for a component or the whole repository against the threat model and security rules, running only authorized deterministic checks, and report prioritized findings with remediation. Manual invocation only; never exposes secrets or performs destructive testing."
argument-hint: "[scope: repo | backend | frontend | ai | infra | ci]"
disable-model-invocation: true
---

# Security Audit

Scope: **$ARGUMENTS** (default `repo`). Read-only unless the owner later
approves specific fixes.

1. **Map the attack surface** for the scope using `docs/SECURITY.md`
   sections 3 and 4 (trust boundaries, threats T-01 to T-18) and the
   relevant control sections. Note which controls are implemented versus planned.
2. **Run available deterministic checks** only; mark missing tools as
   unavailable and never install them:
   - `git check-ignore -v .env` and a search for tracked secret-like files
     (`git ls-files`), reporting names only.
   - `python3 scripts/validate_docs.py --strict` (includes `.env.example` checks).
   - From M1 when present: `gitleaks`, `uv run pip-audit`, `npm audit`;
     from M7: `trivy`.
3. **Review configuration and code** for the scope: authorization,
   sessions and CSRF, input validation, SSRF, logging of sensitive data,
   AI and MCP tool permissions, CI permissions and action pinning, IAM.
   Use the `security-reviewer` agent only for a large scope, on request.
4. **Never** read secret files, print credentials, run exploits, scan
   external hosts, load-test or modify infrastructure.

## Output

Findings ordered Critical, High, Medium, Low, each with location, evidence,
affected threat or requirement, and remediation; a table of checks
(passed, failed, unavailable); and controls verified as working.
This adds the project threat model to the generic `/security-review` command.
