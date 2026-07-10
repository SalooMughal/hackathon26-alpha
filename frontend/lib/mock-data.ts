import type { StandupEntry, TeamMember, TodaySessionResponse } from "./types";

export const HARDCODED_TEAM: TeamMember[] = [
  { id: 1, name: "Shahryar", display_order: 1 },
  { id: 2, name: "Sabir", display_order: 2 },
  { id: 3, name: "Asad", display_order: 3 },
  { id: 4, name: "Zaha", display_order: 4 },
];

const MEMBER_COLORS: Record<number, string> = {
  1: "#1A66FF",
  2: "#0EA5E9",
  3: "#F59E0B",
  4: "#10B981",
};

export function memberColor(memberId: number): string {
  return MEMBER_COLORS[memberId] ?? "#475569";
}

export const SAMPLE_ENTRIES: StandupEntry[] = [
  {
    member_id: 1,
    member_name: "Shahryar",
    yesterday: "Set up the monorepo, Neon project, and shared env templates for the team.",
    today: "Wire frontend to FastAPI, run end-to-end integration, and rehearse the demo.",
    blockers: "None",
    updated_at: "2026-07-10T11:30:00Z",
  },
  {
    member_id: 2,
    member_name: "Sabir",
    yesterday: "Scaffolded FastAPI routers and SQLAlchemy models for sessions and entries.",
    today: "Finish the LangChain summarize endpoint and harden 400/502 error responses.",
    blockers: "Waiting on OpenAI API key quota confirmation",
    updated_at: "2026-07-10T11:32:00Z",
  },
  {
    member_id: 3,
    member_name: "Asad",
    yesterday: "Designed the standup form layout and SummaryPanel component structure.",
    today: "Ship Generate / Regenerate flows, validation, and Copy for Slack.",
    blockers: "None",
    updated_at: "2026-07-10T11:35:00Z",
  },
  {
    member_id: 4,
    member_name: "Zaha",
    yesterday: "Finalized ERD, seed SQL for four team members, and draft system prompt.",
    today: "Tune LangChain prompt for Done / Doing / Blockers and verify sample outputs.",
    blockers: "None",
    updated_at: "2026-07-10T11:38:00Z",
  },
];

export function createMockSession(): TodaySessionResponse {
  const today = new Date().toISOString().slice(0, 10);
  return {
    session: {
      id: "mock-session-550e8400",
      session_date: today,
      status: "draft",
    },
    entries: SAMPLE_ENTRIES.map((entry) => ({ ...entry })),
    summary: null,
  };
}

export function buildMockSummary(
  entries: StandupEntry[],
  version: number,
): string {
  const dateLabel = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  const done = entries
    .map((e) => `• ${e.member_name}: ${tighten(e.yesterday)}`)
    .join("\n");
  const doing = entries
    .map((e) => `• ${e.member_name}: ${tighten(e.today)}`)
    .join("\n");
  const blockers = entries
    .map((e) => {
      const b = normalizeBlocker(e.blockers);
      return `• ${e.member_name}: ${b}`;
    })
    .join("\n");

  return `📋 Daily Standup — ${dateLabel}

✅ Done (Yesterday)
${done}

🔄 Doing (Today)
${doing}

🚧 Blockers
${blockers}`;
}

function tighten(text: string): string {
  const trimmed = text.trim().replace(/\s+/g, " ");
  if (trimmed.length <= 120) return trimmed;
  return `${trimmed.slice(0, 117).trimEnd()}…`;
}

function normalizeBlocker(text: string): string {
  const t = text.trim().toLowerCase();
  if (!t || t === "none" || t === "n/a" || t === "-" || t === "na") {
    return "None";
  }
  return text.trim();
}
