import type { FieldErrors, MemberDraft, UpdateEntryPayload } from "./types";

export function isFilled(value: string): boolean {
  return value.trim().length > 0;
}

export function validateEntry(payload: UpdateEntryPayload): FieldErrors {
  const errors: FieldErrors = {};

  if (!isFilled(payload.yesterday)) {
    errors.yesterday = "Required";
  } else if (payload.yesterday.trim().length > 500) {
    errors.yesterday = "Keep under 500 characters";
  }

  if (!isFilled(payload.today)) {
    errors.today = "Required";
  } else if (payload.today.trim().length > 500) {
    errors.today = "Keep under 500 characters";
  }

  if (!isFilled(payload.blockers)) {
    errors.blockers = 'Required — use "None" if clear';
  } else if (payload.blockers.trim().length > 500) {
    errors.blockers = "Keep under 500 characters";
  }

  return errors;
}

export function hasFieldErrors(errors: FieldErrors): boolean {
  return Boolean(errors.yesterday || errors.today || errors.blockers);
}

export function areAllEntriesComplete(drafts: MemberDraft[]): boolean {
  return drafts.every(
    (d) =>
      isFilled(d.yesterday) &&
      isFilled(d.today) &&
      isFilled(d.blockers) &&
      !hasFieldErrors(d.errors),
  );
}

export function hasUnsavedChanges(drafts: MemberDraft[]): boolean {
  return drafts.some((d) => d.dirty);
}

export function completionCount(drafts: MemberDraft[]): {
  complete: number;
  total: number;
} {
  const complete = drafts.filter(
    (d) => isFilled(d.yesterday) && isFilled(d.today) && isFilled(d.blockers),
  ).length;
  return { complete, total: drafts.length };
}
