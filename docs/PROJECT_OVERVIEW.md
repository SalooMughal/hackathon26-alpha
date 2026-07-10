# Project Overview — AI Standup Bot

## Problem

Teams post scattered standup notes. A lead still has to manually rewrite them into one readable update for Slack. This bot automates that rewrite using AI.

## Solution

1. Load a **hardcoded team** from Neon Postgres (seeded once).
2. Show a Next.js form for each member: **Yesterday / Today / Blockers**.
3. Save entries to Postgres, then call **FastAPI → LangChain → LLM**.
4. Display one formatted summary (section-based: Done / Doing / Blockers).
5. On edit, update the DB row and **regenerate** via a new AI call.

## Hardcoded team

| Name | Hackathon role |
|------|----------------|
| Shahryar | Lead — integration, Neon, demo |
| Sabir | Backend — FastAPI, LangChain |
| Asad | Frontend — Next.js |
| Zaha | Data — schema, seed, prompts |

## Tech stack

- **Next.js** — UI, forms, summary display, Slack copy
- **FastAPI** — API layer, Pydantic models
- **LangChain** — `ChatPromptTemplate` + `ChatOpenAI` / `ChatAnthropic` chain
- **Neon Postgres** — `team_members`, `standup_sessions`, `standup_entries`, `standup_summaries`

## In scope ✅

- Text input only
- One hardcoded team (4 members)
- One summary format (section-based)
- Web page + copy-to-Slack
- Regenerate on edit
- Postgres for current session data (enables regenerate + demo reliability)
- Live demo with ≥ 3 sample inputs

## Out of scope ❌

- Voice transcription
- Scheduling / reminders
- Authentication / multi-user login
- Multi-team support
- Long-term analytics dashboard

## Acceptance criteria (judge checklist)

| # | Criterion | How we prove it |
|---|-----------|-----------------|
| 1 | Full team input | UI shows all 4 members; API rejects incomplete session |
| 2 | Real AI summary | LangChain LLM call in backend logs; output is synthesized prose |
| 3 | Readable output | Done / Doing / Blockers sections; no raw JSON on screen |
| 4 | Live demo | 3+ members with sample text; edit one field → regenerate |

## Summary format

**Section-based** (locked for hackathon):

```
📋 Daily Standup — Friday, Jul 10, 2026

✅ Done (Yesterday)
• Shahryar: …
• Sabir: …

🔄 Doing (Today)
• Asad: …
• Zaha: …

🚧 Blockers
• Shahryar: None
• Sabir: Waiting on API keys
```

## Environment variables

```env
# backend/.env
DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxx.neon.tech/neondb?sslmode=require
OPENAI_API_KEY=sk-...
# or ANTHROPIC_API_KEY=...
AI_PROVIDER=openai          # openai | anthropic
AI_MODEL=gpt-4o-mini        # or claude-3-5-haiku-latest
CORS_ORIGINS=http://localhost:3000

# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Definition of done

- [ ] Neon DB seeded with 4 team members
- [ ] All 4 members can save yesterday / today / blockers
- [ ] LangChain generates a coherent summary (not string-join)
- [ ] Edit + regenerate updates DB and calls AI again
- [ ] Copy-to-Slack produces paste-ready text
- [ ] Demo script runs end-to-end live
