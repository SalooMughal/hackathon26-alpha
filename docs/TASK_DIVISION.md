# Task Division — 4 Person Split

**Stack:** Next.js · FastAPI · LangChain · Neon Postgres  
**Team:** Shahryar (Lead), Sabir, Asad, Zaha

Work in parallel for ~90 minutes, then integrate. Use `docs/API_CONTRACT.md` as the handshake document — do not change request/response shapes without notifying the team.

---

## Shahryar — Lead & Integration

**Owns:** repo scaffold, Neon project, env secrets, end-to-end wiring, demo

| Task | Priority | Est. |
|------|----------|------|
| Create Neon project + share `DATABASE_URL` in team vault | P0 | 15m |
| Monorepo folders: `backend/`, `frontend/`, root `.gitignore` | P0 | 20m |
| FastAPI CORS + health check `GET /health` | P0 | 15m |
| Wire frontend `NEXT_PUBLIC_API_URL` → backend | P0 | 20m |
| Run seed SQL on Neon (or delegate to Zaha, verify) | P0 | 10m |
| Integration test: form → API → DB → LangChain → UI | P0 | 45m |
| Demo rehearsal per `DEMO_SCRIPT.md` | P0 | 30m |
| LangChain prompt review (pair with Zaha) | P1 | 20m |

**Deliverables:** working deployed or local demo, env template, unblock others on ports/URLs

**Blockers to watch:** missing API keys, CORS, wrong `DATABASE_URL` ssl mode

---

## Sabir — Backend (FastAPI + LangChain)

**Owns:** API routes, SQLAlchemy models, LangChain summarization chain

| Task | Priority | Est. |
|------|----------|------|
| FastAPI app skeleton (`app/main.py`, routers) | P0 | 20m |
| SQLAlchemy async models matching `docs/ERD.md` | P0 | 40m |
| `GET /team` — list hardcoded members | P0 | 15m |
| `GET/PUT /sessions/{id}/entries` — read/update standup fields | P0 | 45m |
| `POST /sessions/{id}/summarize` — LangChain chain | P0 | 60m |
| `POST /sessions` — create today's session (or get-or-create) | P1 | 20m |
| Error handling: 400 incomplete entries, 502 AI failure | P1 | 20m |
| Swagger at `/docs` for Asad | P1 | 10m |

**Key files (to create):**

```
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── db.py
│   ├── models/
│   ├── schemas/
│   ├── routers/
│   │   ├── health.py
│   │   ├── team.py
│   │   └── sessions.py           # entries + summarize (per ARCHITECTURE.md)
│   └── services/
│       ├── standup.py
│       └── langchain_summary.py   # LangChain prompt + LLM
├── requirements.txt
└── .env.example
```

**LangChain scope:**

- `ChatPromptTemplate` with system + human messages
- Input: JSON array of `{ name, yesterday, today, blockers }`
- Output: single markdown string (section format)
- **Must not** be `"\n".join()` of raw inputs — prompt must ask for synthesis

**Handoff to Asad:** stable API per `API_CONTRACT.md` by end of block 1

---

## Asad — Frontend (Next.js)

**Owns:** UI, forms, summary panel, regenerate flow, copy-to-Slack

| Task | Priority | Est. |
|------|----------|------|
| `npx create-next-app@latest` (App Router, TS, Tailwind) | P0 | 15m |
| API client module (`lib/api.ts`) | P0 | 20m |
| Page: load team + current session entries | P0 | 30m |
| `StandupForm` — one card per member (yesterday / today / blockers) | P0 | 45m |
| Debounced or explicit Save per member → `PUT` entries | P0 | 30m |
| "Generate Summary" button → `POST /summarize` | P0 | 20m |
| `SummaryPanel` — render markdown, loading + error states | P0 | 30m |
| "Copy for Slack" button (clipboard API) | P1 | 15m |
| "Regenerate" after edit (re-call summarize) | P0 | 15m |
| Basic responsive layout + readable typography | P1 | 30m |

**Key files (to create):**

```
frontend/
├── app/
│   ├── page.tsx              # main standup page
│   ├── layout.tsx
│   └── globals.css
├── components/
│   ├── StandupForm.tsx
│   ├── MemberCard.tsx
│   └── SummaryPanel.tsx
├── lib/
│   └── api.ts
└── .env.local.example
```

**UX flow:**

1. Page loads → fetch team + session entries (pre-fill from seed if empty)
2. User fills/edits fields → save to backend
3. "Generate Summary" → show spinner → display formatted text
4. User edits one field → save → "Regenerate" enabled

**Mock until API ready:** use typed interfaces from `API_CONTRACT.md`

---

## Zaha — Data, Schema & AI Prompt

**Owns:** ERD implementation, seed data, LangChain prompt template, sample demo content

| Task | Priority | Est. |
|------|----------|------|
| Finalize schema in `docs/ERD.md` + `docs/DATABASE.md` | P0 | 30m |
| Write `seed.sql` — 4 team members + optional demo session | P0 | 30m |
| Pair with Sabir on SQLAlchemy model field names | P0 | 15m |
| Author LangChain system prompt in `langchain_summary.py` | P0 | 45m |
| 3+ realistic sample standup texts for demo | P0 | 20m |
| Document prompt versioning in `docs/PROMPT.md` | P1 | 15m |
| Verify AI output format (sections, bullets, no JSON leak) | P0 | 30m |

**Prompt requirements:**

- Merge duplicate themes across people
- Use crisp bullets; max ~2 lines per person per section
- Normalize "none / n/a / -" blockers to "None"
- Include date in header
- Never echo raw JSON

**Seed team (IDs stable for demo):**

| id | name |
|----|------|
| 1 | Shahryar |
| 2 | Sabir |
| 3 | Asad |
| 4 | Zaha |

---

## Integration checklist (all hands)

| Step | Owner | Done |
|------|-------|------|
| Neon DB live + `DATABASE_URL` in backend `.env` | Shahryar | ☐ |
| `seed.sql` applied | Zaha / Shahryar | ☐ |
| `GET /health` returns 200 | Sabir | ☐ |
| `GET /team` returns 4 members | Sabir | ☐ |
| Next.js loads team on `/` | Asad | ☐ |
| Save entry → row in `standup_entries` | Sabir + Asad | ☐ |
| Summarize → LangChain → `standup_summaries` | Sabir + Zaha | ☐ |
| Summary renders in UI | Asad | ☐ |
| Edit + regenerate works | All | ☐ |
| Demo script dry run | Shahryar | ☐ |

## Communication norms

- **API changes** → post in team chat + update `API_CONTRACT.md`
- **Schema changes** → Zaha updates ERD + notify Sabir before migrating
- **Stuck > 15 min** → ping Shahryar for pair debugging
- **Main branch:** small PRs; lead merges during integration hour

## Suggested ports

| Service | Port |
|---------|------|
| Next.js | 3000 |
| FastAPI | 8000 |
| Neon | 5432 (remote) |
