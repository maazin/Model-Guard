# Deploying ModelGuard

## 1. Read-only demo (live now)

`.github/workflows/pages.yml` builds the dashboard in static mode against the committed snapshot in
`apps/web/public/demo-data/` and publishes it to GitHub Pages: **https://maazin.github.io/Model-Guard/**.
Refresh the snapshot after changing the seed or model code:

```bash
make seed && make demo-export && git add apps/web/public/demo-data && git commit -m "Refresh demo snapshot"
```

Mutating actions (approve, resolve, retire, edit) show a "read-only demo" notice; the copilot answer is
precomputed for the default question.

## 2. Fully interactive live stack (needs a host account you own)

`infra/docker/Dockerfile.full` packages the API **and** the built dashboard into one container, so any
single-service host with a PostgreSQL add-on works. The database URL must be `postgresql+psycopg://…`.

### Render (blueprint included)

1. Create a Render account and connect the GitHub repo.
2. *New → Blueprint*, select the repo; Render reads `render.yaml` (web service + free PostgreSQL).
3. First boot runs migrations and seeds the demo (~30 s on the free tier). `MODELGUARD_RESET_ON_START=true`
   restores the seeded state on every restart, so public visitors can approve/reject freely.

Note: Render's `connectionString` is `postgres://…`; SQLAlchemy needs the `postgresql+psycopg://` scheme.
The API normalises this automatically (see `config.py`).

### Fly.io / Railway

Build from `infra/docker/Dockerfile.full`, attach a Postgres, and set the same environment variables as in
`render.yaml`. The container listens on `$PORT` (default 8000).

### What a public live demo exposes

- No secrets or borrower rows: the API never returns dataset rows, and the UCI file (if included in the image)
  is CC BY 4.0 with attribution in the model cards.
- Anyone can act as any demo role; that is intended for a portfolio demo and is why reset-on-start exists.
- Keep `MODELGUARD_LLM_PROVIDER=rule_based` unless you want to pay for hosted copilot calls from strangers.
