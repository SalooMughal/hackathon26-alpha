# StandupBot Frontend

Next.js App Router UI for Team Alpha’s AI Standup Bot.

## Features

- Hardcoded 4-member team forms (Yesterday / Today / Blockers)
- Per-member save with validation
- Generate / Regenerate AI summary
- Copy for Slack
- Auto-fallback to demo data when the API is offline

## Setup

```bash
npm install
cp .env.local.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Environment

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | FastAPI base URL (default `http://localhost:8000`) |
| `NEXT_PUBLIC_USE_MOCK` | Set `true` to force local demo data |

## Stack

- Next.js 16 · React 19 · TypeScript · Tailwind CSS 4
- Plus Jakarta Sans + JetBrains Mono
