# API Contract

**Base URL:** `http://localhost:8000` (dev)  
**Prefix:** `/api`  
**Format:** JSON  
**Auth:** None

FastAPI auto-docs: `http://localhost:8000/docs`

---

## Health

### `GET /health`

```json
{ "status": "ok" }
```

---

## Team

### `GET /api/team`

Returns hardcoded team members (from Postgres seed).

**Response 200:**

```json
{
  "members": [
    { "id": 1, "name": "Shahryar", "display_order": 1 },
    { "id": 2, "name": "Sabir", "display_order": 2 },
    { "id": 3, "name": "Asad", "display_order": 3 },
    { "id": 4, "name": "Zaha", "display_order": 4 }
  ]
}
```

---

## Sessions

### `GET /api/sessions/today`

Get or create today's standup session with all member entries.

**Response 200:**

```json
{
  "session": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "session_date": "2026-07-10",
    "status": "draft"
  },
  "entries": [
    {
      "member_id": 1,
      "member_name": "Shahryar",
      "yesterday": "Set up repo and Neon project.",
      "today": "Integration testing with the team.",
      "blockers": "None",
      "updated_at": "2026-07-10T11:30:00Z"
    }
  ],
  "summary": null
}
```

If a summary exists, include:

```json
"summary": {
  "content": "📋 Daily Standup — ...",
  "version": 2,
  "model": "gpt-4o-mini",
  "created_at": "2026-07-10T12:00:00Z"
}
```

---

### `PUT /api/sessions/{session_id}/entries/{member_id}`

Update one member's standup fields. Creates entry row if missing.

**Request body:**

```json
{
  "yesterday": "Finished FastAPI routes.",
  "today": "LangChain summarize endpoint.",
  "blockers": "Waiting on OpenAI quota"
}
```

**Response 200:** updated entry object (same shape as in `entries[]` above).

**Response 404:** unknown `session_id` or `member_id`

---

### `POST /api/sessions/{session_id}/summarize`

Loads all entries for the session, validates completeness, runs LangChain, saves summary.

**Request body:** empty `{}`

**Response 200:**

```json
{
  "content": "📋 Daily Standup — Friday, Jul 10, 2026\n\n✅ Done (Yesterday)\n• Shahryar: ...",
  "version": 1,
  "model": "gpt-4o-mini",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response 400 — incomplete:**

```json
{
  "detail": "All team members must have yesterday, today, and blockers filled before summarizing."
}
```

**Response 502 — AI failure:**

```json
{
  "detail": "Failed to generate summary. Please try again."
}
```

**Regenerate:** same endpoint — call again after edits; `version` increments.

---

## TypeScript types (for Asad)

```typescript
export interface TeamMember {
  id: number;
  name: string;
  display_order: number;
}

export interface StandupEntry {
  member_id: number;
  member_name: string;
  yesterday: string;
  today: string;
  blockers: string;
  updated_at: string;
}

export interface StandupSummary {
  content: string;
  version: number;
  model: string;
  created_at: string;
}

export interface TodaySessionResponse {
  session: {
    id: string;
    session_date: string;
    status: "draft" | "summarized";
  };
  entries: StandupEntry[];
  summary: StandupSummary | null;
}

export interface UpdateEntryPayload {
  yesterday: string;
  today: string;
  blockers: string;
}
```

---

## CORS

Backend must allow:

```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: GET, PUT, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

---

## Change log

| Date | Change | Author |
|------|--------|--------|
| 2026-07-10 | Initial contract | Team Alpha |
