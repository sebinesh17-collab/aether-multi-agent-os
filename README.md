# Aether Multi-Agent OS

A self-hosted, source-first multi-agent project execution platform. It uses **vanilla HTML/CSS/JavaScript** (no React, no Next.js), FastAPI, PostgreSQL, Redis/RQ, and optional Firebase Storage.

## Agent roster

The repository includes **16,111 individually materialized agent prompt files**:

| Tier | Count | Escalation responsibility |
|---|---:|---|
| Master Leader | 1 | Final, rare, high-impact arbitration |
| Principals | 10 | Cross-department unresolved decisions |
| HODs | 100 | Department-level disputes and policy |
| Leaders | 1,000 | First-level review and consensus |
| Specialists | 15,000 | Execute assigned project tasks |
| **Total** | **16,111** | |

All prompt files contain a role-specific system prompt, operating constraints, escalation rules, evidence requirements, and completion criteria. Agents are profiles that can be scheduled by the orchestrator; they are **not 16,111 continuously running model processes**. Real concurrency is bounded by configured worker count, provider rate limits, machine capacity, and API budget. For decision disputes, the current implementation uses representative panels (5 Leaders, 3 HODs, and 3 Principals) to avoid triggering hundreds or thousands of paid model calls per issue; it does not currently obtain an independent vote from every profile in those tiers.

## What is included

- Project workspace, file uploads, PDF/DOCX/PPTX/XLSX/text extraction, task generation (default minimum 1,000 tasks), execution queue, status tracking, generated UTF-8 artifacts, Markdown results, and downloadable ZIP bundles.
- Role hierarchy and auditable dispute escalation: Leaders → HODs → Principals → the single Master Leader. The Master Leader is only called for critical unresolved decisions.
- OpenAI-compatible provider configuration with encrypted-at-rest API-key vault. Secrets are never returned to the browser after save.
- SMTP completion email; notification is sent when every project task is complete (or a failure summary is sent when terminal failure occurs).
- Optional Firebase Storage adapter. Firebase service-account JSON and bucket are entered through the encrypted settings screen.
- Optional isolated remote terminal service for Python/Node package installation and command execution. It is disabled by default and must be deployed on a separate disposable VM.
- Skillbook documents and a 12-entry built-in tool catalog for file analysis, safe artifact creation, JSON validation, checksums, debates, hierarchical decisions, Firebase uploads, email, and remote terminal execution.

## Quick start (Docker Compose)

1. Install Docker Engine + Docker Compose v2.
2. Copy `.env.example` to `.env`, set strong random values for `JWT_SECRET` and `VAULT_MASTER_KEY`, and set the owner login credentials.
3. Start the stack:

   ```bash
   cp .env.example .env
   # Edit .env before starting
   docker compose up --build -d
   ```
4. Open `http://localhost:8080`, sign in with `OWNER_EMAIL` and `OWNER_PASSWORD`.
5. Open **Settings** and add an OpenAI-compatible provider, Firebase credentials (optional), and SMTP settings.
6. Create a project, upload its brief/source files, set the completion email, and press **Generate & Run**.

The first run creates the database schema and the owner account. Change the initial password immediately after first login.

## Deployment notes

- Put the web app behind HTTPS (Caddy/Nginx/managed TLS) and restrict database/Redis ports to the private network.
- Use managed PostgreSQL/Redis or encrypted persistent volumes with tested backups. Python dependencies are pinned in `backend/requirements.txt`; review and rebuild them regularly, then re-run the included smoke tests. Never expose Postgres, Redis, or the sandbox API to the public internet.
- Set `WORKER_CONCURRENCY` based on provider rate limits and available CPU/RAM. Start with 2–4. Do not set it to 16,111.
- The app does not require AppDeploy, and it does not use React or Next.js.
- The included terminal is intentionally disabled by default. Do not mount the host Docker socket into the public API container. Deploy `sandbox/` on a separate disposable VM with no production credentials, no host mounts, strict egress rules, and frequent rebuilds.
- Configure a real SMTP relay for completion email. Without SMTP settings, project completion is still recorded but email delivery is unavailable.
- Configure a Firebase Storage bucket to store uploaded files remotely. Local uploads are retained in the app volume as a fallback.

See `docs/IMPLEMENTATION-BOUNDARIES.md` for exact limitations of agent voting, tool execution, source analysis, and production hardening.

## Important production boundary

This is a substantial self-hosted implementation scaffold, not a certification that your infrastructure is production-secure or unlimited. Before handling sensitive data or public customers, run security review, penetration tests, load tests, restore tests, and legal/privacy checks. Provider API calls incur provider charges. A 1,000-task run can be expensive and may take a long time; review the generated task plan before enabling execution on real projects.

## Configuration

See `.env.example` and `docs/OPERATIONS.md`. Provider keys and Firebase service-account data should be added in the encrypted Settings UI, not committed to `.env` or source control.
