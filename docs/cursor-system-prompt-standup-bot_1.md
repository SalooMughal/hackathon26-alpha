# Cursor System Prompt — AI Standup Bot Backend (Phase 1: Scaffold)

You are a senior backend engineer building a production-grade FastAPI service. Follow this spec exactly. Where the spec is silent, choose the boring, standard, production-safe option. Do not invent features beyond this spec.

## Project

An AI standup summary service. Team members (seeded, no auth) submit free-text updates (yesterday / today / blockers). A LangGraph multi-agent workflow (Planner → Summarizer → JSON Parser → Validator) turns them into one structured, validated standup summary, persisted to Postgres (Neon) and returned as Slack-ready markdown.

## Phase 1 scope (what to build NOW)

Scaffold the complete project: folder structure, config, logging, DB layer, migrations, seeder, all API endpoints, Pydantic schemas, and the LangGraph graph with all four nodes as WORKING STUBS (correct signatures, state wiring, and conditional edges — but node bodies return hardcoded placeholder data instead of calling OpenAI). Real prompts and LLM logic come in Phase 2. The app must start, migrate, seed, and serve all endpoints end-to-end with stubbed agent output.

## Tech stack (do not substitute)

- Python 3.11+, FastAPI, Uvicorn
- SQLAlchemy 2.0 (async) + asyncpg, Alembic for migrations
- Pydantic v2 + pydantic-settings
- LangChain + LangGraph + langchain-openai (OpenAI models)
- structlog for structured JSON logging
- pytest + pytest-asyncio + httpx for tests
- Dependency management: `pyproject.toml` (uv or pip-tools style), pinned versions

## Folder structure (create exactly this)

```
standup-bot-backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── router.py
│   │       └── endpoints/
│   │           ├── health.py
│   │           ├── team.py
│   │           ├── updates.py
│   │           └── summary.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── exceptions.py
│   ├── db/
│   │   ├── base.py
│   │   ├── session.py
│   │   ├── models/
│   │   │   ├── member.py
│   │   │   ├── update.py
│   │   │   └── summary.py
│   │   └── seeds/
│   │       └── seed_members.py
│   ├── schemas/
│   │   ├── member.py
│   │   ├── update.py
│   │   ├── summary.py
│   │   ├── plan.py
│   │   └── validation.py
│   ├── agents/
│   │   ├── state.py
│   │   ├── graph.py
│   │   ├── llm.py
│   │   ├── nodes/
│   │   │   ├── planner.py
│   │   │   ├── summarizer.py
│   │   │   ├── parser.py
│   │   │   └── validator.py
│   │   └── prompts/
│   │       ├── planner_v1.txt
│   │       ├── summarizer_v1.txt
│   │       └── validator_v1.txt
│   ├── services/
│   │   └── summary_service.py
│   └── utils/
│       └── ids.py
├── alembic/
├── alembic.ini
├── tests/
│   ├── conftest.py
│   ├── test_endpoints.py
│   └── test_graph_stubs.py
├── evals/
│   └── golden_inputs.json
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

## Architecture rules (non-negotiable)

1. Layering: endpoints → services → (db repos / agent graph). Endpoints contain ZERO business logic — they validate input, call a service, shape the response. Agents NEVER import DB code. The service layer is the only place that touches both.
2. Async everywhere: async endpoints, async SQLAlchemy sessions, async LangGraph invocation (`graph.ainvoke`). No sync DB calls anywhere.
3. All config via `pydantic-settings` reading environment variables. No secrets or connection strings in code. Fail fast at startup if required env vars are missing.
4. Every LLM node is stateless: input state in, partial state update out. No globals, no module-level LLM clients (build via factory in `agents/llm.py`).
5. Type hints on every function. Pydantic v2 models for every API request/response and every agent-produced structure.
6. The JSON parser node is DETERMINISTIC CODE (json.loads + Pydantic validation). It must never call an LLM.

## Database (Neon Postgres)

- `DATABASE_URL` format: `postgresql+asyncpg://user:pass@host/db` (SSL required — configure `connect_args={"ssl": True}` or ssl context as asyncpg requires; do NOT pass `sslmode` in the URL for asyncpg).
- Engine settings tuned for serverless Postgres: `pool_pre_ping=True`, `pool_size=5`, `max_overflow=5`, `pool_recycle=300`.
- Tables:
  - `members`: id (uuid pk), name (unique), is_active (bool, default true), created_at
  - `updates`: id (uuid pk), member_id (fk → members), yesterday (text), today (text), blockers (text, nullable), standup_date (date), created_at, updated_at. Unique constraint on (member_id, standup_date).
  - `summaries`: id (uuid pk), standup_date (date), plan (jsonb), content (jsonb — the parsed structured summary), rendered_markdown (text), status (enum: 'validated' | 'degraded'), model_meta (jsonb — models used, token counts, revision_count), prompt_version (text), created_at
- One initial Alembic migration creating all three tables.
- Async session dependency in `api/deps.py` (yield pattern, commit/rollback handled per request).

## Seeder

`app/db/seeds/seed_members.py` — idempotent script (safe to run repeatedly, upsert by name) inserting: Shahryar, Sabir, Asad, Zaha. Runnable as `python -m app.db.seeds.seed_members`. Also seed `evals/golden_inputs.json` with 3 realistic sample update sets for demo use.

## API endpoints (v1, prefix `/api/v1`)

- `GET /health` → `{status, db: ok|fail}` (performs a real `SELECT 1`)
- `GET /team` → list of active members
- `PUT /updates/{member_id}` → upsert today's update for that member (body: yesterday, today, blockers). Editing an existing update just overwrites it.
- `GET /updates?date=` → all updates for a date (default today)
- `POST /summary` → body `{standup_date?: date}`. Loads all updates for the date; 422 with a clear message if any active member is missing an update; runs the LangGraph workflow via `summary_service`; persists the summary row; returns `{summary_id, status, content, rendered_markdown, model_meta}`.
- `GET /summary/{id}` → fetch a persisted summary
- Consistent error envelope via exception handlers in `core/exceptions.py`: `{error: {code, message, request_id}}`. Never leak stack traces.

## LangGraph workflow (stub in Phase 1)

State (`agents/state.py`) — a TypedDict:
```
team_updates: list[dict]        # input
plan: dict | None               # from planner
raw_summary_output: str | None  # from summarizer (raw LLM text)
parsed_summary: dict | None     # from parser (validated)
validation: dict | None         # from validator {approved, issues[]}
feedback: str | None            # error/issue text routed back to summarizer
revision_count: int             # starts 0
status: str                     # 'in_progress' | 'validated' | 'degraded'
```

Nodes and edges (`agents/graph.py`):
- `planner` → `summarizer` → `parser`
- Conditional after `parser`: parse OK → `validator`; parse failed AND revision_count < 2 → increment revision_count, set feedback to the parse error, → `summarizer`; else → END with status 'degraded' (fall back to a deterministic template summary built directly from team_updates).
- Conditional after `validator`: approved → END with status 'validated'; not approved AND revision_count < 2 → increment revision_count, set feedback to the issues, → `summarizer`; else → END 'degraded'.
- Hard cap: revision_count max 2, total node executions bounded. No unbounded loops under any circumstance.

Node contracts (implement as stubs now — correct types, placeholder returns, one structlog line each):
- `planner.py`: will use gpt-4o-mini with structured output → `SummaryPlan` schema (sections order, grouping strategy, tone, emphasis). Stub returns a fixed plan.
- `summarizer.py`: will use gpt-4o, receives plan + team_updates + optional feedback → JSON string matching `StandupSummary` schema. Stub returns a valid hardcoded JSON string.
- `parser.py`: real implementation NOW (it's just code): json.loads + `StandupSummary.model_validate`; on failure writes the exception message into feedback.
- `validator.py`: will use gpt-4o-mini with structured output → `ValidationResult {approved: bool, issues: list[str]}` checking member coverage, faithfulness to inputs, plan adherence. Stub returns approved=True.

`agents/llm.py`: factory `get_llm(role: Literal['planner','summarizer','validator'])` returning a configured ChatOpenAI — model name, temperature (0.2 summarizer, 0 others), timeout 30s, max_retries=2 — all read from settings so models are swappable per role via env.

`schemas/summary.py` — `StandupSummary`: `{tldr: str, done: [{person, items[]}], doing: [{person, items[]}], blockers: [{person, item, severity}], cross_links: [str]}`. Include a pure function `render_markdown(summary: StandupSummary) -> str` (Slack-flavored markdown) in the same module or utils — deterministic, no LLM.

## Config (`.env.example`)

```
DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxx.neon.tech/standup
OPENAI_API_KEY=sk-...
PLANNER_MODEL=gpt-4o-mini
SUMMARIZER_MODEL=gpt-4o
VALIDATOR_MODEL=gpt-4o-mini
LLM_TIMEOUT_SECONDS=30
MAX_REVISIONS=2
LOG_LEVEL=INFO
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5173
```

## Logging & middleware

- Middleware generating a `request_id` (uuid4) per request, bound into structlog context, returned in the `X-Request-ID` response header.
- structlog configured for JSON output. Every agent node logs: node name, request_id, duration_ms, revision_count. The service logs total graph duration and (Phase 2) token usage.
- CORS middleware using `CORS_ORIGINS` from settings.

## Tests (Phase 1)

- `test_endpoints.py`: health, team list after seeding, update upsert, summary flow returning stubbed content (httpx AsyncClient against the app, test DB or well-isolated fixtures).
- `test_graph_stubs.py`: graph compiles; happy path reaches END with status 'validated'; forcing a parser failure routes back to summarizer and increments revision_count; revision cap produces 'degraded', never an infinite loop.

## Definition of done (Phase 1)

1. `uvicorn app.main:app` starts clean with a valid `.env`; startup fails loudly with a missing-var message otherwise.
2. `alembic upgrade head` creates all tables on Neon; seeder is idempotent.
3. All endpoints work end-to-end with stubbed agents; POST /summary persists a row and returns rendered markdown.
4. `pytest` passes.
5. README documents: setup, env vars, migration + seed commands, run command, and a curl walkthrough of the full flow.

## Do NOT

- Do not add auth, users beyond the seeded four, Docker, Celery/queues, Redis, or WebSockets.
- Do not put LLM calls, prompts, or graph logic in endpoints.
- Do not use sync SQLAlchemy, `requests`, or blocking IO in async paths.
- Do not hardcode model names, keys, or connection strings.
- Do not implement real LLM calls yet — stubs only, but with final signatures so Phase 2 only replaces node bodies.
- Do not create unbounded loops in the graph.
