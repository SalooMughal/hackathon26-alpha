"use client";

import { StatusBadge } from "./StatusBadge";

interface AppHeaderProps {
  sessionDate: string | null;
  status: "draft" | "summarized" | null;
  mockMode: boolean;
  apiConnected: boolean;
  dbOk: boolean;
  complete: number;
  total: number;
}

export function AppHeader({
  sessionDate,
  status,
  mockMode,
  apiConnected,
  dbOk,
  complete,
  total,
}: AppHeaderProps) {
  const dateLabel = sessionDate
    ? new Date(`${sessionDate}T12:00:00`).toLocaleDateString("en-US", {
        weekday: "short",
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : "—";

  const progress = total > 0 ? Math.round((complete / total) * 100) : 0;

  return (
    <header
      className="z-50 flex shrink-0 items-center border-b border-[var(--border)] bg-[var(--surface)]/95 shadow-[0_1px_0_rgba(11,31,51,0.04)] backdrop-blur-md"
      style={{ height: "var(--header-h)" }}
    >
      <div className="flex h-full w-full items-center justify-between gap-4 px-4 sm:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-[var(--accent)] text-white shadow-[0_6px_16px_rgba(26,102,255,0.35)]">
            <StandupMark />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h1 className="truncate text-base font-bold tracking-tight text-[var(--ink)]">
                Standup<span className="text-[var(--accent)]">Bot</span>
              </h1>
              <span className="hidden rounded-md bg-[var(--accent-soft)] px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-[var(--accent)] sm:inline">
                Internal
              </span>
            </div>
            <p className="hidden text-xs text-[var(--ink-muted)] sm:block">
              Team Alpha · AI standup workspace
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <div className="hidden items-center gap-2.5 md:flex">
            <div className="h-2 w-28 overflow-hidden rounded-full bg-[var(--surface-muted)] ring-1 ring-[var(--border)]">
              <div
                className="h-full rounded-full bg-gradient-to-r from-[var(--accent)] to-[#0ea5e9] transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
            <span className="text-xs font-semibold tabular-nums text-[var(--ink-muted)]">
              {complete}/{total}
            </span>
          </div>

          <span className="hidden h-5 w-px bg-[var(--border)] md:block" />

          {mockMode ? (
            <StatusBadge label="Demo" tone="warning" />
          ) : apiConnected ? (
            <StatusBadge
              label={dbOk ? "Live" : "API only"}
              tone={dbOk ? "success" : "warning"}
            />
          ) : null}
          <StatusBadge label={dateLabel} tone="neutral" />
          {status ? (
            <StatusBadge
              label={status === "summarized" ? "Summarized" : "Draft"}
              tone={status === "summarized" ? "success" : "info"}
            />
          ) : null}
        </div>
      </div>
    </header>
  );
}

function StandupMark() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M4 7.5h16M4 12h11M4 16.5h14"
        stroke="currentColor"
        strokeWidth="2.4"
        strokeLinecap="round"
      />
    </svg>
  );
}
