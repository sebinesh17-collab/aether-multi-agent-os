# Operations and deployment

## Required values

Generate secrets with a cryptographically secure source. Example:

```bash
python -c "import secrets,base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"
```

Use the output for both `JWT_SECRET` (or a separate long random string) and `VAULT_MASTER_KEY` only as documented. Keep `.env` mode `0600`, exclude it from backups that are not encrypted, and rotate keys with a planned re-encryption migration. If you lose `VAULT_MASTER_KEY`, encrypted provider/Firebase credentials cannot be recovered.

## Task economics and throughput

The default planner materializes at least 1,000 tasks. Each task can make a model call. Configure provider spend limits and rate limits. Start with 1–2 workers; measure task latency, token usage, retries, and error rates before scaling. 16,111 agent profiles are not the same as 16,111 concurrent workers.

## Backups

Back up Postgres and `/data` consistently. Test restore to a clean environment. Store backup encryption keys separately. Use managed object storage lifecycle policies for uploaded files and artifacts.

## Security checklist

- HTTPS only; set `CORS_ORIGINS` to the exact frontend origin.
- Use strong owner password and rotate it after first login.
- Keep Postgres and Redis on the private network.
- Use a narrow-scope Firebase service account.
- Use SMTP credentials with restricted sending privileges.
- Scan uploaded files and restrict accepted formats in public deployments.
- Run PDF/Office parsers in a constrained environment for untrusted user uploads.
- Do not enable the remote terminal until it runs on a separate disposable VM.
- Add rate limiting, account lockout, audit retention, and external monitoring before public multi-user exposure.
- Run SAST, dependency scanning, penetration tests, and restore/load tests.

## Current limitations to resolve before public production use

The included implementation has a single owner seed account and no self-service account registration, no billing/tenant administration, and no built-in malware scanner. Agents return structured text artifacts that are materialized into the project artifact directory; this release does not yet provide a full IDE-style patch-apply/diff-review pipeline or automated test execution for every generated artifact. The task planner makes a broad work breakdown; a human should review its plan before launching expensive execution. Task execution is sequential within one project job; multiple jobs may be queued in Redis, but the sample runner does not implement fine-grained distributed task leasing or sophisticated retry/backoff. The provided sandbox is a restricted convenience runner and is not suitable for adversarial multi-tenant workloads without a stronger isolation runtime. SMTP and Firebase are optional and require your own credentials.
