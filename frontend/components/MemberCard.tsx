"use client";

import type { ReactNode } from "react";
import { memberColor } from "@/lib/mock-data";
import type { MemberDraft } from "@/lib/types";
import { isDraftReady } from "@/lib/validation";
import { Button } from "./Button";
import { TextAreaField } from "./TextAreaField";

const ROLE_BY_MEMBER: Record<string, string> = {
  Shahryar: "Lead · Integration",
  Sabir: "Backend · FastAPI",
  Asad: "Frontend · Next.js",
  Zaha: "Data · Schema & prompts",
};

interface MemberCardProps {
  draft: MemberDraft;
  index: number;
  onChange: (
    memberId: string,
    field: "yesterday" | "today" | "blockers",
    value: string,
  ) => void;
  onSave: (memberId: string) => void;
}

export function MemberCard({
  draft,
  index,
  onChange,
  onSave,
}: MemberCardProps) {
  const color = memberColor(draft.member_name);
  const initial = draft.member_name.charAt(0).toUpperCase();
  const role = ROLE_BY_MEMBER[draft.member_name] ?? "Team member";

  const isComplete = isDraftReady(draft);

  return (
    <article
      className="member-card group relative overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-[0_1px_2px_rgba(11,31,51,0.04),0_8px_24px_rgba(11,31,51,0.05)] transition-all duration-300 hover:-translate-y-0.5 hover:border-[var(--border-strong)] hover:shadow-[0_8px_28px_rgba(11,31,51,0.1)]"
      style={{ animationDelay: `${index * 70}ms` }}
    >
      <div
        className="absolute inset-y-0 left-0 w-1.5"
        style={{ background: color }}
        aria-hidden
      />

      <div className="flex items-center justify-between gap-4 border-b border-[var(--border)] bg-gradient-to-r from-[var(--surface-muted)]/80 to-transparent py-4 pl-6 pr-4 sm:pl-7 sm:pr-5">
        <div className="flex min-w-0 items-center gap-3.5">
          <div className="relative shrink-0">
            <div
              className="flex size-12 items-center justify-center rounded-2xl text-base font-bold text-white shadow-[0_4px_14px_rgba(11,31,51,0.18)]"
              style={{ background: color }}
              aria-hidden
            >
              {initial}
            </div>
            <span
              className={`absolute -bottom-0.5 -right-0.5 size-3.5 rounded-full border-2 border-white ${
                isComplete
                  ? "bg-[var(--success)]"
                  : draft.dirty
                    ? "bg-[var(--warning)]"
                    : "bg-[var(--border-strong)]"
              }`}
              title={
                isComplete ? "Complete" : draft.dirty ? "Unsaved" : "Incomplete"
              }
            />
          </div>

          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="truncate text-base font-bold tracking-tight text-[var(--ink)]">
                {draft.member_name}
              </h3>
              <MemberStatus
                dirty={draft.dirty}
                complete={Boolean(isComplete)}
                saving={draft.saving}
              />
            </div>
            <p className="mt-0.5 truncate text-[13px] text-[var(--ink-muted)]">
              {role}
            </p>
          </div>
        </div>

        <div className="flex shrink-0 flex-col items-end gap-2 sm:flex-row sm:items-center sm:gap-3">
          <FieldProgress
            filled={
              [
                draft.yesterday.trim(),
                draft.today.trim(),
                draft.blockers.trim() || "None",
              ].filter(Boolean).length
            }
          />
          <div className="flex items-center gap-2.5">
            <span className="hidden text-xs text-[var(--ink-faint)] lg:inline">
              {draft.dirty
                ? "Unsaved"
                : draft.savedAt
                  ? `Saved ${formatTime(draft.savedAt)}`
                  : "Not saved"}
            </span>
            <Button
              size="sm"
              variant={draft.dirty ? "primary" : "secondary"}
              loading={draft.saving}
              disabled={!draft.dirty || draft.saving}
              onClick={() => onSave(draft.member_id)}
            >
              Save
            </Button>
          </div>
        </div>
      </div>

      <div className="grid gap-3 p-4 sm:grid-cols-3 sm:gap-3 sm:p-5 sm:pl-7">
        <FieldZone tone="yesterday">
          <TextAreaField
            label="Yesterday"
            icon={<IconCheck />}
            placeholder="What did you complete?"
            value={draft.yesterday}
            error={draft.errors.yesterday}
            rows={4}
            onChange={(e) =>
              onChange(draft.member_id, "yesterday", e.target.value)
            }
          />
        </FieldZone>
        <FieldZone tone="today">
          <TextAreaField
            label="Today"
            icon={<IconBolt />}
            placeholder="What will you focus on?"
            value={draft.today}
            error={draft.errors.today}
            rows={4}
            onChange={(e) =>
              onChange(draft.member_id, "today", e.target.value)
            }
          />
        </FieldZone>
        <FieldZone tone="blockers">
          <TextAreaField
            label="Blockers"
            icon={<IconAlert />}
            hint='Use "None" if clear'
            placeholder="Anything in your way?"
            value={draft.blockers}
            error={draft.errors.blockers}
            rows={4}
            onChange={(e) =>
              onChange(draft.member_id, "blockers", e.target.value)
            }
          />
        </FieldZone>
      </div>
    </article>
  );
}

function FieldZone({
  tone,
  children,
}: {
  tone: "yesterday" | "today" | "blockers";
  children: ReactNode;
}) {
  const tones = {
    yesterday: {
      bg: "bg-[rgba(14,165,233,0.06)]",
      border: "border-[rgba(14,165,233,0.18)]",
    },
    today: {
      bg: "bg-[rgba(26,102,255,0.06)]",
      border: "border-[rgba(26,102,255,0.18)]",
    },
    blockers: {
      bg: "bg-[rgba(245,158,11,0.07)]",
      border: "border-[rgba(245,158,11,0.2)]",
    },
  }[tone];

  return (
    <div
      className={`rounded-xl border p-3.5 transition-colors ${tones.bg} ${tones.border}`}
    >
      {children}
    </div>
  );
}

function FieldProgress({ filled }: { filled: number }) {
  return (
    <div
      className="flex items-center gap-1"
      title={`${filled}/3 fields filled`}
      aria-label={`${filled} of 3 fields filled`}
    >
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className={`h-1.5 w-5 rounded-full transition-colors ${
            i < filled ? "bg-[var(--accent)]" : "bg-[var(--border)]"
          }`}
        />
      ))}
    </div>
  );
}

function MemberStatus({
  dirty,
  complete,
  saving,
}: {
  dirty: boolean;
  complete: boolean;
  saving: boolean;
}) {
  if (saving) {
    return (
      <span className="rounded-full bg-[var(--surface-muted)] px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-[var(--ink-muted)]">
        Saving…
      </span>
    );
  }
  if (dirty) {
    return (
      <span className="rounded-full bg-[var(--warning-soft)] px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-[var(--warning)]">
        Edited
      </span>
    );
  }
  if (complete) {
    return (
      <span className="rounded-full bg-[var(--success-soft)] px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-[var(--success)]">
        Ready
      </span>
    );
  }
  return (
    <span className="rounded-full bg-[var(--surface-muted)] px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-[var(--ink-faint)]">
      Incomplete
    </span>
  );
}

function IconCheck() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M5 13l4 4L19 7"
        stroke="currentColor"
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function IconBolt() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M13 2L4 14h7l-1 8 10-14h-7l0-6z" fill="currentColor" />
    </svg>
  );
}

function IconAlert() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M12 9v4M12 17h.01M10.3 4.3L2.8 17.2A2 2 0 004.5 20h15a2 2 0 001.7-2.8L13.7 4.3a2 2 0 00-3.4 0z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}
