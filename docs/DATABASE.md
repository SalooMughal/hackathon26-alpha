# Database — Neon Postgres

## Setup (Shahryar)

1. Create project at [neon.tech](https://neon.tech)
2. Copy connection string (pooled recommended for serverless)
3. Convert to SQLAlchemy async URL:

```
postgresql+asyncpg://USER:PASSWORD@ep-xxx.region.aws.neon.tech/neondb?ssl=require
```

4. Add to `backend/.env` as `DATABASE_URL`

## DDL

Run once on Neon SQL editor or via `psql`:

```sql
-- extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- team_members
CREATE TABLE team_members (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(100) NOT NULL UNIQUE,
    display_order INT NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- standup_sessions
CREATE TABLE standup_sessions (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_date DATE NOT NULL UNIQUE,
    status       VARCHAR(20) NOT NULL DEFAULT 'draft'
                 CHECK (status IN ('draft', 'summarized')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- standup_entries
CREATE TABLE standup_entries (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  UUID NOT NULL REFERENCES standup_sessions(id) ON DELETE CASCADE,
    member_id   INT NOT NULL REFERENCES team_members(id),
    yesterday   TEXT NOT NULL DEFAULT '',
    today       TEXT NOT NULL DEFAULT '',
    blockers    TEXT NOT NULL DEFAULT '',
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (session_id, member_id)
);

-- standup_summaries
CREATE TABLE standup_summaries (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  UUID NOT NULL UNIQUE REFERENCES standup_sessions(id) ON DELETE CASCADE,
    content     TEXT NOT NULL,
    model       VARCHAR(50) NOT NULL,
    version     INT NOT NULL DEFAULT 1,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_entries_session ON standup_entries (session_id);
```

## Seed data

```sql
-- Team Alpha (hardcoded)
INSERT INTO team_members (name, display_order) VALUES
    ('Shahryar', 1),
    ('Sabir', 2),
    ('Asad', 3),
    ('Zaha', 4)
ON CONFLICT (name) DO NOTHING;

-- Optional: demo session for today with sample text (Zaha)
-- Adjust session_date to demo day
INSERT INTO standup_sessions (session_date, status)
VALUES (CURRENT_DATE, 'draft')
ON CONFLICT (session_date) DO NOTHING;

-- Populate empty entries for all members in today's session
INSERT INTO standup_entries (session_id, member_id, yesterday, today, blockers)
SELECT s.id, m.id,
    CASE m.name
        WHEN 'Shahryar' THEN 'Created repo structure and Neon database.'
        WHEN 'Sabir'     THEN 'Scaffolded FastAPI app with health endpoint.'
        WHEN 'Asad'      THEN 'Initialized Next.js project with Tailwind.'
        WHEN 'Zaha'      THEN 'Drafted ERD and LangChain system prompt.'
    END,
    CASE m.name
        WHEN 'Shahryar' THEN 'Lead integration and demo prep.'
        WHEN 'Sabir'     THEN 'Build entries API and LangChain summarize route.'
        WHEN 'Asad'      THEN 'Standup form UI and summary panel.'
        WHEN 'Zaha'      THEN 'Finalize seed data and test AI output quality.'
    END,
    CASE m.name
        WHEN 'Shahryar' THEN 'None'
        WHEN 'Sabir'     THEN 'Need OpenAI API key in .env'
        WHEN 'Asad'      THEN 'None'
        WHEN 'Zaha'      THEN 'None'
    END
FROM standup_sessions s
CROSS JOIN team_members m
WHERE s.session_date = CURRENT_DATE
ON CONFLICT (session_id, member_id) DO NOTHING;
```

## Migrations (optional stretch)

For hackathon speed, raw SQL in Neon console is fine. If Sabir has time:

```bash
pip install alembic
alembic init alembic
# generate revision from SQLAlchemy models
```

## Connection notes

- Use **pooled** connection string for FastAPI on Render/Railway
- Use `pool_pre_ping=True` in SQLAlchemy engine
- Neon free tier: sufficient for demo

## Useful queries

```sql
-- Verify seed
SELECT * FROM team_members ORDER BY display_order;

-- Today's entries
SELECT m.name, e.yesterday, e.today, e.blockers
FROM standup_entries e
JOIN team_members m ON m.id = e.member_id
JOIN standup_sessions s ON s.id = e.session_id
WHERE s.session_date = CURRENT_DATE;

-- Latest summary
SELECT content, version, model FROM standup_summaries ss
JOIN standup_sessions s ON s.id = ss.session_id
WHERE s.session_date = CURRENT_DATE;
```
