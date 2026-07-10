import type { FieldErrors, MemberDraft, UpdateEntryPayload } from "./types";

export function isFilled(value: string): boolean {
  return value.trim().length > 0;
}

/** Normalize blockers for display, validation, and API payloads. */
export function normalizeBlockers(value: string | null | undefined): string {
  const trimmed = (value ?? "").trim();
  if (!trimmed) return "None";
  const lower = trimmed.toLowerCase();
  if (lower === "n/a" || lower === "na" || lower === "-") return "None";
  return trimmed;
}

export function validateEntry(payload: UpdateEntryPayload): FieldErrors {
  const errors: FieldErrors = {};
  const blockers = normalizeBlockers(payload.blockers);

  if (!isFilled(payload.yesterday)) {
    errors.yesterday = "Required";
  }

  if (!isFilled(payload.today)) {
    errors.today = "Required";
  }

  if (!isFilled(blockers)) {
    errors.blockers = 'Required — use "None" if clear';
  }

  return errors;
}

export function hasFieldErrors(errors: FieldErrors): boolean {
  return Boolean(errors.yesterday || errors.today || errors.blockers);
}

export function isDraftReady(draft: MemberDraft): boolean {
  const blockers = normalizeBlockers(draft.blockers);
  return (
    isFilled(draft.yesterday) &&
    isFilled(draft.today) &&
    isFilled(blockers) &&
    !hasFieldErrors(
      validateEntry({
        yesterday: draft.yesterday,
        today: draft.today,
        blockers,
      }),
    )
  );
}

export function areAllEntriesComplete(drafts: MemberDraft[]): boolean {
  return drafts.length > 0 && drafts.every(isDraftReady);
}

export function hasUnsavedChanges(drafts: MemberDraft[]): boolean {
  return drafts.some((d) => d.dirty);
}

export function completionCount(drafts: MemberDraft[]): {
  complete: number;
  total: number;
} {
  const complete = drafts.filter(isDraftReady).length;
  return { complete, total: drafts.length };
}

export function savedReadyCount(drafts: MemberDraft[]): {
  ready: number;
  total: number;
} {
  const ready = drafts.filter(
    (d) => isDraftReady(d) && !d.dirty && Boolean(d.savedAt),
  ).length;
  return { ready, total: drafts.length };
}

export function incompleteMemberNames(drafts: MemberDraft[]): string[] {
  return drafts.filter((d) => !isDraftReady(d)).map((d) => d.member_name);
}
