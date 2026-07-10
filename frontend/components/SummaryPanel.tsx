"use client";

import { Button } from "./Button";
import { StatusBadge } from "./StatusBadge";

interface SummaryPanelProps {
  content: string | null;
  version: number | null;
  model: string | null;
  loading: boolean;
  error: string | null;
  canGenerate: boolean;
  hasSummary: boolean;
  hasUnsaved: boolean;
  onGenerate: () => void;
  onCopy: () => void;
  copied: boolean;
  docked?: boolean;
}

export function SummaryPanel({
  content,
  version,
  model,
  loading,
  error,
  canGenerate,
  hasSummary,
  hasUnsaved,
  onGenerate,
  onCopy,
  copied,
  docked = false,
}: SummaryPanelProps) {
  return (
    <aside
      className={`flex flex-col bg-[var(--surface)] ${
        docked
          ? "h-full min-h-0"
          : "min-h-[520px] overflow-hidden rounded-2xl border border-[var(--border)] shadow-[0_8px_28px_rgba(11,31,51,0.08)]"
      }`}
    >
      {/* Compact header + actions — keep summary area large */}
      <div className="shrink-0 border-b border-[var(--border)] px-4 py-3 sm:px-5">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h2 className="text-[15px] font-bold tracking-tight text-[var(--ink)]">
                AI summary
              </h2>
              {version != null ? (
                <StatusBadge label={`v${version}`} tone="accent" />
              ) : null}
            </div>
            <p className="truncate text-xs text-[var(--ink-muted)]">
              Slack-ready digest
              {model ? ` · ${model}` : ""}
            </p>
          </div>
        </div>

        <div className="mt-3 flex gap-2">
          <Button
            size="md"
            className="min-w-0 flex-1"
            loading={loading}
            disabled={!canGenerate || loading || hasUnsaved}
            onClick={onGenerate}
          >
            {hasSummary ? "Regenerate" : "Generate"}
          </Button>
          <Button
            variant="secondary"
            size="md"
            className="min-w-0 flex-1"
            disabled={!content || loading}
            onClick={onCopy}
          >
            {copied ? "Copied!" : "Copy"}
          </Button>
        </div>

        {hasUnsaved ? (
          <p className="mt-2 text-center text-xs font-medium text-[var(--warning)]">
            Save all member cards first
          </p>
        ) : !canGenerate && !loading ? (
          <p className="mt-2 text-center text-xs text-[var(--ink-muted)]">
            Complete every field to unlock
          </p>
        ) : null}
      </div>

      {/* Primary reading surface — takes remaining height */}
      <div className="summary-scroll min-h-0 flex-1 overflow-y-auto overscroll-contain p-4 sm:p-5">
        {loading ? (
          <LoadingState />
        ) : error ? (
          <ErrorState message={error} />
        ) : content ? (
          <div className="summary-body animate-fade-in min-h-full rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] p-5 sm:p-6">
            <pre className="whitespace-pre-wrap break-words font-[family-name:var(--font-body)] text-[15px] leading-[1.75] text-[var(--ink)] sm:text-[16px] sm:leading-[1.8]">
              {content}
            </pre>
          </div>
        ) : (
          <EmptyState />
        )}
      </div>
    </aside>
  );
}

function EmptyState() {
  return (
    <div className="flex h-full min-h-[280px] flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-[var(--border-strong)] bg-gradient-to-b from-[var(--surface-muted)] to-white px-5 text-center">
      <div className="flex size-12 items-center justify-center rounded-2xl bg-[var(--accent-soft)] text-[var(--accent)] shadow-sm">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden>
          <path
            d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"
            stroke="currentColor"
            strokeWidth="2.2"
            strokeLinecap="round"
          />
        </svg>
      </div>
      <div>
        <p className="font-bold text-[var(--ink)]">No summary yet</p>
        <p className="mt-1 max-w-[220px] text-[13px] text-[var(--ink-muted)]">
          Fill the team forms, then hit Generate for a Done / Doing / Blockers
          digest.
        </p>
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="flex h-full min-h-[280px] flex-col items-center justify-center gap-4">
      <div className="relative size-12">
        <span className="absolute inset-0 animate-ping rounded-full bg-[var(--accent)]/20" />
        <span className="absolute inset-1.5 animate-spin rounded-full border-2 border-[var(--accent)] border-r-transparent" />
      </div>
      <div className="text-center">
        <p className="font-bold text-[var(--ink)]">Generating with AI…</p>
        <p className="mt-1 text-[13px] text-[var(--ink-muted)]">
          Synthesizing Done, Doing & Blockers
        </p>
      </div>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-[var(--danger-border)] bg-[var(--danger-soft)] px-4 py-5 text-center">
      <p className="font-bold text-[var(--danger)]">Summary failed</p>
      <p className="mt-1 text-[13px] text-[var(--danger)]/85">{message}</p>
    </div>
  );
}
