import {
  buildMockSummary,
  createMockSession,
  HARDCODED_TEAM,
} from "./mock-data";
import {
  ApiError,
  type StandupEntry,
  type StandupSummary,
  type SummarizeResponse,
  type TeamMember,
  type TodaySessionResponse,
  type UpdateEntryPayload,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Set true to force offline demo without backend */
const FORCE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

let mockMode = FORCE_MOCK;
let mockSession: TodaySessionResponse | null = null;
let mockSummaryVersion = 0;

export function isMockMode(): boolean {
  return mockMode;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  if (FORCE_MOCK) {
    throw new ApiError("Mock mode enabled", 0);
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
    });
  } catch {
    throw new ApiError("Cannot reach server. Is the API running?", 0);
  }

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      /* ignore parse errors */
    }
    throw new ApiError(detail, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export async function getTeam(): Promise<TeamMember[]> {
  try {
    const data = await request<{ members: TeamMember[] }>("/api/team");
    mockMode = false;
    return data.members.sort((a, b) => a.display_order - b.display_order);
  } catch {
    mockMode = true;
    return [...HARDCODED_TEAM];
  }
}

export async function getTodaySession(): Promise<TodaySessionResponse> {
  try {
    const data = await request<TodaySessionResponse>("/api/sessions/today");
    mockMode = false;
    return data;
  } catch {
    mockMode = true;
    if (!mockSession) {
      mockSession = createMockSession();
    }
    return structuredClone(mockSession);
  }
}

export async function updateEntry(
  sessionId: string,
  memberId: number,
  payload: UpdateEntryPayload,
): Promise<StandupEntry> {
  if (mockMode) {
    if (!mockSession) mockSession = createMockSession();
    const idx = mockSession.entries.findIndex((e) => e.member_id === memberId);
    const member = HARDCODED_TEAM.find((m) => m.id === memberId);
    const updated: StandupEntry = {
      member_id: memberId,
      member_name: member?.name ?? `Member ${memberId}`,
      yesterday: payload.yesterday,
      today: payload.today,
      blockers: payload.blockers,
      updated_at: new Date().toISOString(),
    };
    if (idx >= 0) {
      mockSession.entries[idx] = updated;
    } else {
      mockSession.entries.push(updated);
    }
    mockSession.session.status = "draft";
    await delay(280);
    return updated;
  }

  return request<StandupEntry>(
    `/api/sessions/${sessionId}/entries/${memberId}`,
    {
      method: "PUT",
      body: JSON.stringify(payload),
    },
  );
}

export async function summarize(sessionId: string): Promise<SummarizeResponse> {
  if (mockMode) {
    if (!mockSession) mockSession = createMockSession();
    const incomplete = mockSession.entries.some(
      (e) =>
        !e.yesterday.trim() || !e.today.trim() || !e.blockers.trim(),
    );
    if (incomplete || mockSession.entries.length < HARDCODED_TEAM.length) {
      throw new ApiError(
        "All team members must have yesterday, today, and blockers filled before summarizing.",
        400,
      );
    }
    await delay(900);
    mockSummaryVersion += 1;
    const content = buildMockSummary(mockSession.entries, mockSummaryVersion);
    const summary: StandupSummary = {
      content,
      version: mockSummaryVersion,
      model: "mock-local",
      created_at: new Date().toISOString(),
    };
    mockSession.summary = summary;
    mockSession.session.status = "summarized";
    return {
      content,
      version: mockSummaryVersion,
      model: "mock-local",
      session_id: sessionId,
    };
  }

  return request<SummarizeResponse>(`/api/sessions/${sessionId}/summarize`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
