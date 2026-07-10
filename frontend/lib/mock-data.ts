import type { StandupUpdate, TeamMember, UpdatesListResponse } from "./types";

export const HARDCODED_TEAM: TeamMember[] = [
  {
    id: "mock-shahryar",
    name: "Shahryar",
    is_active: true,
    created_at: "2026-07-10T12:00:00Z",
  },
  {
    id: "mock-sabir",
    name: "Sabir",
    is_active: true,
    created_at: "2026-07-10T12:00:00Z",
  },
  {
    id: "mock-asad",
    name: "Asad",
    is_active: true,
    created_at: "2026-07-10T12:00:00Z",
  },
  {
    id: "mock-zaha",
    name: "Zaha",
    is_active: true,
    created_at: "2026-07-10T12:00:00Z",
  },
];

const MEMBER_COLORS: Record<string, string> = {
  Shahryar: "#1A66FF",
  Sabir: "#0EA5E9",
  Asad: "#F59E0B",
  Zaha: "#10B981",
};

export function memberColor(memberName: string): string {
  return MEMBER_COLORS[memberName] ?? "#475569";
}

const SAMPLE_UPDATES: Omit<StandupUpdate, "standup_date">[] = [
  {
    id: "mock-u1",
    member_id: "mock-shahryar",
    member_name: "Shahryar",
    yesterday:
      "Set up the monorepo, Neon project, and shared env templates for the team.",
    today:
      "Wire frontend to FastAPI, run end-to-end integration, and rehearse the demo.",
    blockers: "None",
    updated_at: "2026-07-10T11:30:00Z",
  },
  {
    id: "mock-u2",
    member_id: "mock-sabir",
    member_name: "Sabir",
    yesterday:
      "Scaffolded FastAPI routers and SQLAlchemy models for sessions and entries.",
    today:
      "Finish the LangChain summarize endpoint and harden 400/502 error responses.",
    blockers: "Waiting on OpenAI API key quota confirmation",
    updated_at: "2026-07-10T11:32:00Z",
  },
  {
    id: "mock-u3",
    member_id: "mock-asad",
    member_name: "Asad",
    yesterday:
      "Designed the standup form layout and SummaryPanel component structure.",
    today: "Ship Generate / Regenerate flows, validation, and Copy for Slack.",
    blockers: "None",
    updated_at: "2026-07-10T11:35:00Z",
  },
  {
    id: "mock-u4",
    member_id: "mock-zaha",
    member_name: "Zaha",
    yesterday:
      "Finalized ERD, seed SQL for four team members, and draft system prompt.",
    today:
      "Tune LangChain prompt for Done / Doing / Blockers and verify sample outputs.",
    blockers: "None",
    updated_at: "2026-07-10T11:38:00Z",
  },
];

export function createMockWorkspace(): UpdatesListResponse {
  const standup_date = new Date().toISOString().slice(0, 10);
  return {
    standup_date,
    updates: SAMPLE_UPDATES.map((u) => ({ ...u, standup_date })),
  };
}

export function buildMockSummary(
  updates: StandupUpdate[],
  version: number,
): string {
  const dateLabel = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  const done = updates
    .map((u) => `• ${u.member_name}: ${tighten(u.yesterday)}`)
    .join("\n");
  const doing = updates
    .map((u) => `• ${u.member_name}: ${tighten(u.today)}`)
    .join("\n");
  const blockers = updates
    .map((u) => {
      const b = normalizeBlocker(u.blockers ?? "");
      return `• ${u.member_name}: ${b}`;
    })
    .join("\n");

  return `📋 Daily Standup — ${dateLabel}

✅ Done (Yesterday)
${done}

🔄 Doing (Today)
${doing}

🚧 Blockers
${blockers}

— mock v${version}`;
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
