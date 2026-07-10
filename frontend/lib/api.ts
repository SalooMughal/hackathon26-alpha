import {
  buildMockSummary,
  createMockWorkspace,
  HARDCODED_TEAM,
} from "./mock-data";
import {
  parseIncompleteUpdateMessage,
} from "./api-errors";
import { normalizeBlockers } from "./validation";
import {
  ApiError,
  type HealthResponse,
  type MemberDraft,
  type StandupUpdate,
  type SummaryDetailResponse,
  type SummaryResponse,
  type SummaryState,
  type TeamMember,
  type UpdateEntryPayload,
  type UpdatesListResponse,
  type ApiErrorBody,
  type FieldErrors,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const FORCE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

let mockMode = FORCE_MOCK;
let mockStandupDate: string | null = null;
let mockUpdates: StandupUpdate[] = [];
let mockSummary: SummaryState | null = null;
let mockGenerateCount = 0;

export function isMockMode(): boolean {
  return mockMode;
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function parseErrorMessage(status: number, body: ApiErrorBody): string {
  if (body.error?.message) return body.error.message;
  return `Request failed (${status})`;
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
    let message = `Request failed (${response.status})`;
    let code: string | null = null;
    let fieldErrors: FieldErrors | undefined;
    try {
      const body = (await response.json()) as ApiErrorBody;
      message = parseErrorMessage(response.status, body);
      code = body.error?.code ?? null;
      if (code === "incomplete_update") {
        fieldErrors = parseIncompleteUpdateMessage(message);
      }
    } catch {
      /* ignore parse errors */
    }
    throw new ApiError(message, response.status, code, fieldErrors);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export async function checkHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export async function getTeam(): Promise<TeamMember[]> {
  try {
    const data = await request<{ members: TeamMember[] }>("/api/v1/team");
    mockMode = false;
    return data.members
      .filter((m) => m.is_active)
      .sort((a, b) => a.name.localeCompare(b.name));
  } catch {
    mockMode = true;
    return [...HARDCODED_TEAM];
  }
}

export async function getUpdates(
  standupDate?: string,
): Promise<UpdatesListResponse> {
  if (mockMode) {
    if (!mockStandupDate) {
      const workspace = createMockWorkspace();
      mockStandupDate = workspace.standup_date;
      mockUpdates = workspace.updates;
    }
    return {
      standup_date: mockStandupDate,
      updates: structuredClone(mockUpdates),
    };
  }

  const query = standupDate ? `?standup_date=${standupDate}` : "";
  return request<UpdatesListResponse>(`/api/v1/updates${query}`);
}

export async function updateEntry(
  memberId: string,
  payload: UpdateEntryPayload,
): Promise<StandupUpdate> {
  if (mockMode) {
    const member = HARDCODED_TEAM.find((m) => m.id === memberId);
    const updated: StandupUpdate = {
      id: `mock-update-${memberId}`,
      member_id: memberId,
      member_name: member?.name ?? "Member",
      yesterday: payload.yesterday,
      today: payload.today,
      blockers: payload.blockers,
      standup_date: mockStandupDate ?? todayIso(),
      updated_at: new Date().toISOString(),
    };
    const idx = mockUpdates.findIndex((u) => u.member_id === memberId);
    if (idx >= 0) mockUpdates[idx] = updated;
    else mockUpdates.push(updated);
    mockSummary = null;
    await delay(280);
    return updated;
  }

  return request<StandupUpdate>(`/api/v1/updates/${memberId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  }).catch((err: unknown) => {
    if (err instanceof ApiError && err.code === "incomplete_update") {
      err.memberId = memberId;
    }
    throw err;
  });
}

export async function createSummary(
  standupDate?: string,
): Promise<SummaryState> {
  if (mockMode) {
    const incomplete = mockUpdates.some(
      (u) =>
        !u.yesterday.trim() ||
        !u.today.trim() ||
        (u.blockers ?? "").trim().length === 0,
    );
    if (incomplete || mockUpdates.length < HARDCODED_TEAM.length) {
      throw new ApiError(
        "All team members must have yesterday, today, and blockers filled before summarizing.",
        422,
        "incomplete_updates",
      );
    }
    await delay(900);
    mockGenerateCount += 1;
    const content = buildMockSummary(mockUpdates, mockGenerateCount);
    mockSummary = {
      summaryId: `mock-summary-${mockGenerateCount}`,
      content,
      status: "validated",
      model: "mock-local",
      version: mockGenerateCount,
      createdAt: new Date().toISOString(),
    };
    return mockSummary;
  }

  const body = standupDate ? { standup_date: standupDate } : {};
  const result = await request<SummaryResponse>("/api/v1/summary", {
    method: "POST",
    body: JSON.stringify(body),
  });
  return mapSummaryResponse(result);
}

export async function getSummary(summaryId: string): Promise<SummaryState> {
  if (mockMode && mockSummary?.summaryId === summaryId) {
    return mockSummary;
  }

  const result = await request<SummaryDetailResponse>(
    `/api/v1/summary/${summaryId}`,
  );
  return mapSummaryDetail(result);
}

function mapSummaryResponse(result: SummaryResponse): SummaryState {
  const revision = result.model_meta?.revision_count ?? 0;
  return {
    summaryId: result.summary_id,
    content: result.rendered_markdown,
    status: result.status,
    model: result.model_meta?.models?.summarizer ?? null,
    version: revision + 1,
    createdAt: new Date().toISOString(),
  };
}

function mapSummaryDetail(result: SummaryDetailResponse): SummaryState {
  const revision = result.model_meta?.revision_count ?? 0;
  return {
    summaryId: result.id,
    content: result.rendered_markdown,
    status: result.status,
    model: result.model_meta?.models?.summarizer ?? null,
    version: revision + 1,
    createdAt: result.created_at,
  };
}

/** Merge team list with saved updates into editable drafts */
export function buildDraftsFromWorkspace(
  team: TeamMember[],
  updates: StandupUpdate[],
): MemberDraft[] {
  return team.map((member) => {
    const update = updates.find((u) => u.member_id === member.id);
    return {
      member_id: member.id,
      member_name: member.name,
      yesterday: update?.yesterday ?? "",
      today: update?.today ?? "",
      blockers: normalizeBlockers(update?.blockers),
      dirty: false,
      saving: false,
      savedAt: update?.updated_at ?? null,
      errors: {},
    };
  });
}

const SUMMARY_STORAGE_KEY = "standupbot:last-summary";

export function loadStoredSummaryId(standupDate: string): string | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(SUMMARY_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { date: string; summaryId: string };
    return parsed.date === standupDate ? parsed.summaryId : null;
  } catch {
    return null;
  }
}

export function storeSummaryId(standupDate: string, summaryId: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(
    SUMMARY_STORAGE_KEY,
    JSON.stringify({ date: standupDate, summaryId }),
  );
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
