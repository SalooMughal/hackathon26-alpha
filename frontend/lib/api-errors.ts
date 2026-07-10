import type { FieldErrors } from "./types";

const FIELD_MARKERS = ["yesterday", "today", "blockers"] as const;

/** Parse backend `incomplete_update` message into per-field hints. */
export function parseIncompleteUpdateMessage(message: string): FieldErrors {
  const errors: FieldErrors = {};
  const lower = message.toLowerCase();

  for (const field of FIELD_MARKERS) {
    const marker = `${field}:`;
    const idx = lower.indexOf(marker);
    if (idx === -1) continue;

    const start = idx + marker.length;
    let end = message.length;

    for (const other of FIELD_MARKERS) {
      if (other === field) continue;
      const otherIdx = lower.indexOf(`${other}:`, start);
      if (otherIdx !== -1 && otherIdx < end) {
        end = otherIdx;
      }
    }

    const text = message.slice(start, end).trim().replace(/\.\s*$/, "");
    if (text) {
      errors[field] = text;
    }
  }

  return errors;
}

/** First sentence for toasts — avoids dumping the full multi-field message. */
export function apiErrorToastMessage(message: string): string {
  const match = message.match(/^[^.]+\./);
  return match ? match[0].trim() : message;
}
