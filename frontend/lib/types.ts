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

export interface SummarizeResponse {
  content: string;
  version: number;
  model: string;
  session_id: string;
}

export interface FieldErrors {
  yesterday?: string;
  today?: string;
  blockers?: string;
}

export type MemberDraft = UpdateEntryPayload & {
  member_id: number;
  member_name: string;
  dirty: boolean;
  saving: boolean;
  savedAt: string | null;
  errors: FieldErrors;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}
