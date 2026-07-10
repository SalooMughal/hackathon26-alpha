# Standup Bot Backend

FastAPI backend for the AI Standup Bot hackathon project (Team Alpha).

## Phase 1 status

This scaffold includes project structure, config, logging, DB models, Alembic migration, seeder, API route stubs, and LangGraph agent stubs. Business logic and full workflow wiring come in Phase 2.

## Requirements

- Python 3.11+
- Neon Postgres (or local Postgres for dev)
- OpenAI API key (required at startup even before LLM calls are wired)

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Edit .env with your DATABASE_URL and OPENAI_API_KEY
```

## Database

```bash
# Run migrations
alembic upgrade head

# Seed team members (idempotent)
python -m app.db.seeds.seed_members
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

## Endpoints (scaffold)

| Method | Path | Status |
|--------|------|--------|
| GET | `/health` | Working (SELECT 1) |
| GET | `/api/v1/team` | Stub — Phase 2 |
| PUT | `/api/v1/updates/{member_id}` | Stub — Phase 2 |
| GET | `/api/v1/updates?date=` | Stub — Phase 2 |
| POST | `/api/v1/summary` | Stub — Phase 2 |
| GET | `/api/v1/summary/{id}` | Stub — Phase 2 |

## Environment variables

See `.env.example` for all settings. Required at startup:

- `DATABASE_URL` — `postgresql+asyncpg://...` (do not use `sslmode` in URL; SSL is set via connect_args)
- `OPENAI_API_KEY`

## Tests

```bash
pytest
```

Most tests are skipped until Phase 2 wiring is complete.

## Project structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app, middleware, CORS
│   ├── api/                 # Route handlers (thin layer)
│   ├── core/                # Config, logging, exceptions
│   ├── db/                  # SQLAlchemy models, session, seeds
│   ├── schemas/             # Pydantic request/response models
│   ├── agents/              # LangGraph stubs (Phase 2)
│   ├── services/            # Business logic layer
│   └── utils/
├── alembic/                 # Migrations
├── tests/
├── evals/                   # Golden demo inputs
└── pyproject.toml
```
