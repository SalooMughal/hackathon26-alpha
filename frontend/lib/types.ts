/** Backend-aligned types for /api/v1 */

export interface TeamMember {
  id: string;
  name: string;
  is_active: boolean;
  created_at: string;
}

export interface StandupUpdate {
  id: string;
  member_id: string;
  member_name: string | null;
  yesterday: string;
  today: string;
  blockers: string | null;
  standup_date: string;
  updated_at: string;
}

export interface UpdatesListResponse {
  standup_date: string;
  updates: StandupUpdate[];
}

export interface UpdateEntryPayload {
  yesterday: string;
  today: string;
  blockers: string | null;
}

export interface PersonItems {
  person: string;
  items: string[];
}

export interface BlockerItem {
  person: string;
  item: string;
  severity: "low" | "medium" | "high";
}

export interface StandupSummaryContent {
  tldr: string;
  done: PersonItems[];
  doing: PersonItems[];
  blockers: BlockerItem[];
  cross_links: string[];
}

export interface SummaryModelMeta {
  models?: Record<string, string>;
  revision_count?: number;
  usage_total?: { input_tokens: number; output_tokens: number };
  graph_duration_ms?: number;
  error?: string | null;
}

export interface SummaryResponse {
  summary_id: string;
  status: "validated" | "degraded";
  content: StandupSummaryContent;
  rendered_markdown: string;
  model_meta: SummaryModelMeta;
}

export interface SummaryDetailResponse extends SummaryResponse {
  id: string;
  standup_date: string;
  prompt_version: string;
  created_at: string;
}

/** UI state for the summary panel */
export interface SummaryState {
  summaryId: string;
  content: string;
  status: "validated" | "degraded";
  model: string | null;
  version: number;
  createdAt: string | null;
}

export interface HealthResponse {
  status: string;
  db: string;
}

export interface FieldErrors {
  yesterday?: string;
  today?: string;
  blockers?: string;
}

export type MemberDraft = {
  member_id: string;
  member_name: string;
  yesterday: string;
  today: string;
  blockers: string;
  dirty: boolean;
  saving: boolean;
  savedAt: string | null;
  errors: FieldErrors;
};

export interface ApiErrorBody {
  error?: {
    code: string;
    message: string;
    request_id?: string | null;
  };
}

export class ApiError extends Error {
  status: number;
  code: string | null;
  fieldErrors?: FieldErrors;
  memberId?: string;

  constructor(
    message: string,
    status: number,
    code: string | null = null,
    fieldErrors?: FieldErrors,
    memberId?: string,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.fieldErrors = fieldErrors;
    this.memberId = memberId;
  }
}
