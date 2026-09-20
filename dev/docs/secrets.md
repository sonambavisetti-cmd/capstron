Secrets Management Policy (Vinayaka File Works)

Overview
- Use environment variables for all runtime secrets in all environments.
- Local development may use a `.env` file but this file MUST be added to `.gitignore` and never committed.
- Production must use a managed secret store (e.g., AWS Secrets Manager, Azure Key Vault). Documented rotation policy required.

Local Development
- Keep `.env.example` in repo with placeholder values.
- Use python-dotenv only for local convenience. CI and production must rely on environment variables or a secrets provider.

CI / Pre-deploy
- A secret-scan script (`scripts/secret_scan.sh`) runs in CI early to detect obvious leaks.
- The CI pipeline must fail if secret-scan detects potential secrets.

Production
- Use a managed secret store. Access credentials should be delivered to the runtime via environment variables injected securely by deployment tooling.
- Rotate credentials every 90 days by default.
- Audit access to secrets via cloud provider audit logs.

Developer Guidance
- Never paste API keys or private keys into code or comments.
- If a secret is accidentally committed, rotate it immediately and remove it from repo history.
- Use scoped, least-privilege credentials for services (do not use root account keys).

Contact
- Security Owner: @devops
- For emergency rotations, follow the runbook in `dev/ops/`.
