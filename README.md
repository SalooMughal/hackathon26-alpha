# Team Alpha — AI Standup Bot

A hackathon tool that collects free-text standup updates from a hardcoded team and uses **LangChain + an LLM** to produce one clean, channel-ready daily summary.

**Team:** Shahryar (Lead), Sabir, Asad, Zaha

## Quick links

| Doc | Purpose |
|-----|---------|
| [Project Overview](docs/PROJECT_OVERVIEW.md) | Goals, scope, acceptance criteria |
| [Task Division](docs/TASK_DIVISION.md) | Who owns what — 4-person split |
| [ERD](docs/ERD.md) | Postgres schema & entity relationships |
| [Architecture](docs/ARCHITECTURE.md) | System design & tech stack |
| [API Contract](docs/API_CONTRACT.md) | FastAPI endpoints & payloads |
| [Database](docs/DATABASE.md) | Neon setup, migrations, seed SQL |
| [Demo Script](docs/DEMO_SCRIPT.md) | Live demo flow for judges |

## Tech stack

| Layer | Choice |
|-------|--------|
| Frontend | **Next.js** (App Router) — forms, summary UI, copy-to-Slack |
| Backend | **FastAPI** — REST API, validation |
| AI | **LangChain** — prompt chain → OpenAI or Anthropic |
| Database | **Neon Postgres** — team seed, standup entries, summaries |

## Repo layout (planned)

```
hackathon26-alpha/
├── backend/          # FastAPI + LangChain + SQLAlchemy
├── frontend/         # Next.js
├── docs/             # Planning & contracts
└── README.md
```

## Getting started (after scaffold)

```bash
# 1. Neon — create project, copy connection string

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill DATABASE_URL, OPENAI_API_KEY
uvicorn app.main:app --reload --port 8000

# 3. Frontend
cd frontend
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

## Status

🚧 **Planning phase** — read `docs/TASK_DIVISION.md` and pick your workstream before coding.
