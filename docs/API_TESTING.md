# API Testing Guide

**Base URL (local):** `http://127.0.0.1:8000`  
**API prefix:** `/api/v1`  
**Auth:** None  
**Header (PUT/POST):** `Content-Type: application/json`

Interactive docs: `http://127.0.0.1:8000/docs`

---

## Recommended test order

1. `GET /health`
2. `GET /api/v1/team` — copy each member `id`
3. `PUT /api/v1/updates/{member_id}` — once per team member (all 4)
4. `GET /api/v1/updates` — verify all entries saved
5. `POST /api/v1/summary` — runs the AI pipeline
6. `GET /api/v1/summary/{summary_id}` — fetch persisted result

---

## 1. Health check

| | |
|---|---|
| **Method** | `GET` |
| **URL** | `http://127.0.0.1:8000/health` |
| **Body** | none |

### Response `200`

```json
{
  "status": "ok",
  "db": "ok"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Always `"ok"` when the app is running |
| `db` | string | `"ok"` if DB connection works, `"fail"` otherwise |

---

## 2. List team

| | |
|---|---|
| **Method** | `GET` |
| **URL** | `http://127.0.0.1:8000/api/v1/team` |
| **Body** | none |

### Response `200`

```json
{
  "members": [
    {
      "id": "08a32298-5923-4ba3-8a1a-8e575f1eadc0",
      "name": "Shahryar",
      "is_active": true,
      "created_at": "2026-07-10T12:55:32.944271Z"
    },
    {
      "id": "eae23a72-0074-4503-a50e-d0c31bf74d40",
      "name": "Sabir",
      "is_active": true,
      "created_at": "2026-07-10T12:55:32.944271Z"
    },
    {
      "id": "a87a8709-ba36-4508-a628-581bb2d553f9",
      "name": "Asad",
      "is_active": true,
      "created_at": "2026-07-10T12:55:32.944271Z"
    },
    {
      "id": "2db20519-1721-4658-bf07-b5a7ac5d2b4e",
      "name": "Zaha",
      "is_active": true,
      "created_at": "2026-07-10T12:55:32.944271Z"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `members[].id` | UUID | Use in `PUT /updates/{member_id}` |
| `members[].name` | string | Hardcoded team member name |
| `members[].is_active` | boolean | Only active members are required for summary |
| `members[].created_at` | datetime | ISO 8601 timestamp |

---

## 3. Upsert standup update

| | |
|---|---|
| **Method** | `PUT` |
| **URL** | `http://127.0.0.1:8000/api/v1/updates/{member_id}` |
| **Path param** | `member_id` — UUID from `GET /team` |

### Request body

```json
{
  "yesterday": "Created repo structure and Neon database.",
  "today": "Lead integration and demo prep.",
  "blockers": "None"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `yesterday` | string | yes | What the member did yesterday (min 1 char) |
| `today` | string | yes | What the member is doing today (min 1 char) |
| `blockers` | string \| null | no | Blockers text; use `"None"` or `null` if none |

### Example URLs (replace IDs from your `GET /team` response)

```
PUT http://127.0.0.1:8000/api/v1/updates/08a32298-5923-4ba3-8a1a-8e575f1eadc0   # Shahryar
PUT http://127.0.0.1:8000/api/v1/updates/eae23a72-0074-4503-a50e-d0c31bf74d40   # Sabir
PUT http://127.0.0.1:8000/api/v1/updates/a87a8709-ba36-4508-a628-581bb2d553f9   # Asad
PUT http://127.0.0.1:8000/api/v1/updates/2db20519-1721-4658-bf07-b5a7ac5d2b4e   # Zaha
```

### Sample payloads per member

**Shahryar**

```json
{
  "yesterday": "Created repo structure and Neon database.",
  "today": "Lead integration and demo prep.",
  "blockers": "None"
}
```

**Sabir**

```json
{
  "yesterday": "Scaffolded FastAPI app and LangGraph pipeline.",
  "today": "Build summarize endpoint and test with Postman.",
  "blockers": "Need OpenAI API key quota"
}
```

**Asad**

```json
{
  "yesterday": "Initialized Next.js project with Tailwind.",
  "today": "Standup form UI and summary panel.",
  "blockers": "None"
}
```

**Zaha**

```json
{
  "yesterday": "Drafted ERD and agent prompts.",
  "today": "Finalize seed data and test AI output quality.",
  "blockers": "None"
}
```

### Response `200`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "member_id": "eae23a72-0074-4503-a50e-d0c31bf74d40",
  "member_name": "Sabir",
  "yesterday": "Scaffolded FastAPI app and LangGraph pipeline.",
  "today": "Build summarize endpoint and test with Postman.",
  "blockers": "Need OpenAI API key quota",
  "standup_date": "2026-07-10",
  "updated_at": "2026-07-10T13:00:00.000000Z"
}
```

### Error `404`

```json
{
  "error": {
    "code": "not_found",
    "message": "Member {uuid} not found or inactive",
    "request_id": "..."
  }
}
```

---

## 4. List updates for a date

| | |
|---|---|
| **Method** | `GET` |
| **URL** | `http://127.0.0.1:8000/api/v1/updates` |
| **Query param** | `date` (optional) — `YYYY-MM-DD`; defaults to today |

### Example

```
GET http://127.0.0.1:8000/api/v1/updates
GET http://127.0.0.1:8000/api/v1/updates?date=2026-07-10
```

### Response `200`

```json
{
  "standup_date": "2026-07-10",
  "updates": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "member_id": "eae23a72-0074-4503-a50e-d0c31bf74d40",
      "member_name": "Sabir",
      "yesterday": "Scaffolded FastAPI app and LangGraph pipeline.",
      "today": "Build summarize endpoint and test with Postman.",
      "blockers": "Need OpenAI API key quota",
      "standup_date": "2026-07-10",
      "updated_at": "2026-07-10T13:00:00.000000Z"
    }
  ]
}
```

---

## 5. Generate summary (AI pipeline)

Runs: **sanitizer → planner → summarizer → parser → validator**

| | |
|---|---|
| **Method** | `POST` |
| **URL** | `http://127.0.0.1:8000/api/v1/summary` |

### Request body

Empty object (uses today's date):

```json
{}
```

Or with an explicit date:

```json
{
  "standup_date": "2026-07-10"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `standup_date` | date (string) | no | Defaults to today if omitted |

**Prerequisite:** All active team members must have `yesterday` and `today` filled for that date.

### Response `200`

```json
{
  "summary_id": "660e8400-e29b-41d4-a716-446655440099",
  "status": "validated",
  "content": {
    "tldr": "Sabir is blocked on OpenAI quota while the team progresses on backend and UI.",
    "done": [
      {
        "person": "Shahryar",
        "items": ["Created repo structure and Neon database"]
      },
      {
        "person": "Sabir",
        "items": ["Scaffolded FastAPI app and LangGraph pipeline"]
      }
    ],
    "doing": [
      {
        "person": "Asad",
        "items": ["Standup form UI and summary panel"]
      }
    ],
    "blockers": [
      {
        "person": "Sabir",
        "item": "Need OpenAI API key quota",
        "severity": "medium"
      }
    ],
    "cross_links": []
  },
  "rendered_markdown": "📋 Daily Standup — 2026-07-10\n\nSabir is blocked on...\n\n*Done (Yesterday)*\n\n• Shahryar: ...",
  "model_meta": {
    "models": {
      "sanitizer": "gpt-4o-mini",
      "planner": "gpt-4o-mini",
      "summarizer": "gpt-4o",
      "validator": "gpt-4o-mini"
    },
    "revision_count": 0,
    "usage": {
      "sanitizer": { "input_tokens": 400, "output_tokens": 200 },
      "planner": { "input_tokens": 350, "output_tokens": 80 },
      "summarizer": { "input_tokens": 600, "output_tokens": 250 },
      "validator": { "input_tokens": 500, "output_tokens": 40 }
    },
    "usage_total": { "input_tokens": 1850, "output_tokens": 570 },
    "sanitizer_flags": {
      "Sabir": []
    },
    "graph_duration_ms": 12500,
    "error": null
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `summary_id` | UUID | Use in `GET /summary/{id}` |
| `status` | `"validated"` \| `"degraded"` | `"validated"` = passed validator; `"degraded"` = fallback summary |
| `content` | object | Structured standup summary (see below) |
| `rendered_markdown` | string | Slack-ready formatted text |
| `model_meta` | object | Models used, token usage, sanitizer flags, timing |

#### `content` shape

| Field | Type | Description |
|-------|------|-------------|
| `tldr` | string | One-line summary for the team lead |
| `done` | array | `{ person, items[] }` — yesterday's work |
| `doing` | array | `{ person, items[] }` — today's work |
| `blockers` | array | `{ person, item, severity }` — severity: `low` \| `medium` \| `high` |
| `cross_links` | array | Related work between members |

### Error `422` — incomplete updates

```json
{
  "error": {
    "code": "incomplete_updates",
    "message": "All team members must have yesterday, today, and blockers filled before summarizing. Missing or incomplete: Asad",
    "request_id": "..."
  }
}
```

### Error `500` — pipeline failure

```json
{
  "error": {
    "code": "internal_error",
    "message": "Internal server error",
    "request_id": "..."
  }
}
```

---

## 6. Get summary by ID

| | |
|---|---|
| **Method** | `GET` |
| **URL** | `http://127.0.0.1:8000/api/v1/summary/{summary_id}` |
| **Path param** | `summary_id` — UUID from `POST /summary` response |

### Example

```
GET http://127.0.0.1:8000/api/v1/summary/660e8400-e29b-41d4-a716-446655440099
```

### Response `200`

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440099",
  "standup_date": "2026-07-10",
  "status": "validated",
  "content": {
    "tldr": "Sabir is blocked on OpenAI quota while the team progresses on backend and UI.",
    "done": [{ "person": "Shahryar", "items": ["Created repo structure and Neon database"] }],
    "doing": [{ "person": "Asad", "items": ["Standup form UI and summary panel"] }],
    "blockers": [{ "person": "Sabir", "item": "Need OpenAI API key quota", "severity": "medium" }],
    "cross_links": []
  },
  "rendered_markdown": "📋 Daily Standup — 2026-07-10\n\n...",
  "model_meta": { "models": {}, "revision_count": 0, "usage": {} },
  "prompt_version": "v1",
  "created_at": "2026-07-10T13:05:00.000000Z"
}
```

### Error `404`

```json
{
  "error": {
    "code": "not_found",
    "message": "Summary {uuid} not found",
    "request_id": "..."
  }
}
```

---

## Error envelope (all endpoints)

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "request_id": "string | null"
  }
}
```

Common codes: `not_found`, `incomplete_updates`, `validation_error`, `internal_error`
