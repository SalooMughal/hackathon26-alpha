# Standup Bot Backend

FastAPI backend with a multi-agent LangGraph pipeline for AI standup summaries.

## Pipeline

```
sanitizer → planner → summarizer → parser → validator → END
                              ↑ retry (bounded) ↑
                              fallback (degraded)
```

- **Sanitizer** — input guardrail (fail-open on LLM error)
- **Planner** — structured summary plan (`gpt-4o-mini`)
- **Summarizer** — JSON summary output (`gpt-4o`)
- **Parser** — deterministic `json.loads` + Pydantic validation
- **Validator** — faithfulness check (`gpt-4o-mini`)
- **Fallback** — deterministic template when validation fails

## Requirements

- Python 3.11+
- Neon Postgres
- OpenAI API key

## Setup

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Set DATABASE_URL and OPENAI_API_KEY
alembic upgrade head
python -m app.db.seeds.seed_members
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

## API (prefix `/api/v1`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness + DB check |
| GET | `/team` | Active members |
| PUT | `/updates/{member_id}` | Upsert today's update |
| GET | `/updates?date=` | List updates for a date |
| POST | `/summary` | Run full agent pipeline |
| GET | `/summary/{id}` | Fetch persisted summary |

## Tests

```bash
pytest
```

## Live evals (requires real OpenAI key)

```bash
python -m evals.run_evals
```

## Curl walkthrough

```bash
# List team
curl http://localhost:8000/api/v1/team

# Upsert update (use member UUID from /team)
curl -X PUT http://localhost:8000/api/v1/updates/{member_id} \
  -H "Content-Type: application/json" \
  -d '{"yesterday":"Built API","today":"LangGraph pipeline","blockers":"None"}'

# Generate summary (all members must have yesterday + today filled)
curl -X POST http://localhost:8000/api/v1/summary \
  -H "Content-Type: application/json" \
  -d '{}'
```
