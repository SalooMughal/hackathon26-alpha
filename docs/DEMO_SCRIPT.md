# Demo Script — Judge Presentation (~5 min)

**Presenter:** Shahryar  
**Backup:** Sabir (API), Asad (UI), Zaha (explain AI prompt)

## Pre-demo checklist

- [ ] Backend running on `:8000` — `GET /health` → ok
- [ ] Frontend running on `:3000`
- [ ] Neon seeded with 4 team members
- [ ] `OPENAI_API_KEY` set and tested once
- [ ] Browser tab open to standup page (zoom 125% for visibility)

## Script

### 1. Problem (30 sec)

> "Our team posts standup notes in different formats. I still rewrite them manually for Slack. We built a bot that collects everyone's updates and uses LangChain + an LLM to produce one clean summary."

### 2. Show team form (45 sec)

- Point out **4 hardcoded members** — Shahryar, Sabir, Asad, Zaha
- Each card has **Yesterday / Today / Blockers**
- Mention data is stored in **Neon Postgres** (not just browser memory)

### 3. Pre-filled sample data (30 sec)

- Show 3–4 members already filled (from seed or typed earlier)
- Read one example aloud briefly

### 4. Generate summary (60 sec)

- Click **"Generate Summary"**
- Show loading state
- **Open Network tab** (optional): `POST /api/sessions/.../summarize`
- Summary appears with **Done / Doing / Blockers** sections
- Call out: "This is AI-synthesized — notice it's not a copy-paste of what we typed"

### 5. Regenerate (45 sec)

- Edit **Sabir's blocker** field (e.g. change to "Resolved API key issue")
- Save → click **Regenerate**
- Show updated Blockers section and `version` increment if visible

### 6. Copy to Slack (30 sec)

- Click **Copy for Slack**
- Paste into a text editor or Slack draft — show it's ready to post

### 7. Architecture flash (30 sec, optional)

Show `docs/ARCHITECTURE.md` diagram or say:

> "Next.js frontend → FastAPI → LangChain → OpenAI, with Neon Postgres for entries and summaries."

### 8. Close (15 sec)

> "Single team, no auth, built for hackathon speed — but real AI, real database, regenerate on edit."

## Fallback if AI fails live

1. Show last successful summary from DB (if seeded)
2. Explain: "We have error handling; retry usually works"
3. Show `/docs` Swagger and invoke summarize manually

## Judge Q&A prep

| Question | Answer |
|----------|--------|
| Is it really AI? | Yes — LangChain invokes OpenAI; prompt in `PROMPT.md` |
| Why Postgres? | Persist entries + support regenerate; demo reliability |
| Multi-team? | Out of scope — one hardcoded team |
| Auth? | Out of scope — hackathon demo |
