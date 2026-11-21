# System architecture

```text
Browser (vanilla HTML/CSS/JS)
        | HTTPS + JWT
        v
FastAPI API ---- PostgreSQL (users, projects, files, tasks, decisions, audit)
        |                     |
        +---- Redis/RQ -------+---- Worker ---- OpenAI-compatible provider
        |                                  |--- encrypted secret vault
        |                                  |--- SMTP completion notice
        |                                  |--- Firebase Storage (optional)
        +---- Remote sandbox API (optional, separately isolated VM)
```

The hierarchy is stored as role-specific prompt profiles. Work is assigned to specialists; disagreements are routed through leadership tiers. The decision record stores proposals, each tier's response, the final resolution, and the escalation path. Uploaded documents are evidence inputs, not policy sources. They cannot override system prompts or tool authorization.
