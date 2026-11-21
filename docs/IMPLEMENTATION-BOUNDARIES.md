# Implementation boundaries for this release

This is a source-code delivery intended for self-hosting and staged hardening. Do not treat a successful Docker startup as production certification.

## Agent execution

- The repository includes 16,111 full role-specific prompt profiles, indexed and loadable by ID. They are definitions, not 16,111 permanently running processes.
- A project start creates at least 1,000 persisted task records and queues one RQ project job. The current worker processes that project's tasks sequentially and performs one provider call per task. This can be expensive and take a long time.
- The current task runner asks the model for structured JSON and saves valid text/code artifacts into `/data/artifacts/project_<id>`. It does not yet provide an IDE-grade multi-file patch review, git branch/commit automation, automatic compile/test pipeline, or autonomous self-correction loop.
- Uploaded PDF/DOCX/PPTX/XLSX and text files are parsed for text. Scanned-image OCR is not implemented. The worker selects bounded text excerpts relevant to each task; it does not send arbitrarily large source files in full.
- The remote cloud terminal is currently invoked by the owner from Settings. The task worker does not automatically execute model-suggested shell commands. This avoids silently running generated shell commands. A later release can add an explicit per-project command approval workflow.

## Leadership and disputes

- Agent prompts and role counts are exact: 1 Master, 10 Principals, 100 HODs, 1,000 Leaders, and 15,000 Specialists.
- To limit paid calls, the dispute resolver currently uses a representative panel of 5 Leaders, 3 HODs, and 3 Principals. It does not ask every Leader/HOD/Principal profile to independently vote.
- The Master Leader is unique and called only when the owner marks a dispute critical and all prior representative panels return escalation. Otherwise, unresolved matters go to owner review.

## Before public production

Add rate limiting and login throttling, review browser token storage and XSS risk, enable file malware scanning, use a hardened sandbox runtime, deploy database migrations, implement audit retention and backups/restore tests, add observability and alerting, run independent security/load tests, and verify email delivery. Configure HTTPS, strong secrets, provider billing limits, SMTP, Firebase service-account credentials, and the remote terminal on a separate disposable VM.
