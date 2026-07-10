"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getTeam,
  getTodaySession,
  isMockMode,
  summarize,
  updateEntry,
} from "@/lib/api";
import { HARDCODED_TEAM } from "@/lib/mock-data";
import type { MemberDraft, StandupSummary } from "@/lib/types";
import { ApiError } from "@/lib/types";
import {
  areAllEntriesComplete,
  completionCount,
  hasUnsavedChanges,
  validateEntry,
} from "@/lib/validation";
import { AppHeader } from "@/components/AppHeader";
import { StandupForm } from "@/components/StandupForm";
import { SummaryPanel } from "@/components/SummaryPanel";
import { Toast } from "@/components/Toast";
import { Button } from "@/components/Button";

export default function HomePage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionDate, setSessionDate] = useState<string | null>(null);
  const [status, setStatus] = useState<"draft" | "summarized" | null>(null);
  const [drafts, setDrafts] = useState<MemberDraft[]>([]);
  const [summary, setSummary] = useState<StandupSummary | null>(null);
  const [mockMode, setMockMode] = useState(false);
  const [loadingPage, setLoadingPage] = useState(true);
  const [pageError, setPageError] = useState<string | null>(null);
  const [summarizing, setSummarizing] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [toastTone, setToastTone] = useState<"success" | "error" | "info">(
    "success",
  );
  const [copied, setCopied] = useState(false);

  const showToast = useCallback(
    (message: string, tone: "success" | "error" | "info" = "success") => {
      setToast(message);
      setToastTone(tone);
      window.setTimeout(() => setToast(null), 2600);
    },
    [],
  );

  const load = useCallback(async () => {
    setLoadingPage(true);
    setPageError(null);
    try {
      const [team, session] = await Promise.all([
        getTeam(),
        getTodaySession(),
      ]);
      setMockMode(isMockMode());
      setSessionId(session.session.id);
      setSessionDate(session.session.session_date);
      setStatus(session.session.status);
      setSummary(session.summary);

      const members = team.length ? team : HARDCODED_TEAM;
      const nextDrafts: MemberDraft[] = members
        .slice()
        .sort((a, b) => a.display_order - b.display_order)
        .map((member) => {
          const entry = session.entries.find((e) => e.member_id === member.id);
          return {
            member_id: member.id,
            member_name: member.name,
            yesterday: entry?.yesterday ?? "",
            today: entry?.today ?? "",
            blockers: entry?.blockers ?? "",
            dirty: false,
            saving: false,
            savedAt: entry?.updated_at ?? null,
            errors: {},
          };
        });
      setDrafts(nextDrafts);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to load standup";
      setPageError(message);
    } finally {
      setLoadingPage(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const onChange = useCallback(
    (
      memberId: number,
      field: "yesterday" | "today" | "blockers",
      value: string,
    ) => {
      setDrafts((prev) =>
        prev.map((d) => {
          if (d.member_id !== memberId) return d;
          const next = { ...d, [field]: value, dirty: true };
          next.errors = validateEntry({
            yesterday: next.yesterday,
            today: next.today,
            blockers: next.blockers,
          });
          return next;
        }),
      );
      setSummaryError(null);
    },
    [],
  );

  const onSave = useCallback(
    async (memberId: number) => {
      if (!sessionId) return;

      const draft = drafts.find((d) => d.member_id === memberId);
      if (!draft) return;

      const errors = validateEntry(draft);
      if (Object.keys(errors).length) {
        setDrafts((prev) =>
          prev.map((d) => (d.member_id === memberId ? { ...d, errors } : d)),
        );
        showToast("Fix validation errors before saving", "error");
        return;
      }

      setDrafts((prev) =>
        prev.map((d) =>
          d.member_id === memberId ? { ...d, saving: true } : d,
        ),
      );

      try {
        const updated = await updateEntry(sessionId, memberId, {
          yesterday: draft.yesterday.trim(),
          today: draft.today.trim(),
          blockers: draft.blockers.trim(),
        });
        setDrafts((prev) =>
          prev.map((d) =>
            d.member_id === memberId
              ? {
                  ...d,
                  yesterday: updated.yesterday,
                  today: updated.today,
                  blockers: updated.blockers,
                  dirty: false,
                  saving: false,
                  savedAt: updated.updated_at,
                  errors: {},
                }
              : d,
          ),
        );
        setStatus("draft");
        showToast(`Saved ${draft.member_name}'s update`);
      } catch (err) {
        setDrafts((prev) =>
          prev.map((d) =>
            d.member_id === memberId ? { ...d, saving: false } : d,
          ),
        );
        const message =
          err instanceof ApiError ? err.message : "Failed to save entry";
        showToast(message, "error");
      }
    },
    [drafts, sessionId, showToast],
  );

  const onGenerate = useCallback(async () => {
    if (!sessionId) return;

    const validated = drafts.map((d) => ({
      ...d,
      errors: validateEntry(d),
    }));
    setDrafts(validated);

    if (!areAllEntriesComplete(validated)) {
      setSummaryError("Fill all fields for every teammate before summarizing.");
      showToast("Complete all teammate fields", "error");
      return;
    }

    if (hasUnsavedChanges(validated)) {
      showToast("Save all cards first", "error");
      return;
    }

    setSummarizing(true);
    setSummaryError(null);

    try {
      const result = await summarize(sessionId);
      setSummary({
        content: result.content,
        version: result.version,
        model: result.model,
        created_at: new Date().toISOString(),
      });
      setStatus("summarized");
      showToast(
        summary ? "Summary regenerated" : "Summary generated",
        "success",
      );
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : "Failed to generate summary. Please try again.";
      setSummaryError(message);
      showToast(message, "error");
    } finally {
      setSummarizing(false);
    }
  }, [drafts, sessionId, showToast, summary]);

  const onCopy = useCallback(async () => {
    if (!summary?.content) return;
    try {
      await navigator.clipboard.writeText(summary.content);
      setCopied(true);
      showToast("Copied — paste into Slack");
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      showToast("Clipboard unavailable", "error");
    }
  }, [showToast, summary]);

  const { complete, total } = useMemo(
    () => completionCount(drafts),
    [drafts],
  );

  const canGenerate = areAllEntriesComplete(drafts) && drafts.length > 0;
  const hasUnsaved = hasUnsavedChanges(drafts);

  const summaryProps = {
    content: summary?.content ?? null,
    version: summary?.version ?? null,
    model: summary?.model ?? null,
    loading: summarizing,
    error: summaryError,
    canGenerate,
    hasSummary: Boolean(summary),
    hasUnsaved,
    onGenerate: () => void onGenerate(),
    onCopy: () => void onCopy(),
    copied,
  };

  if (loadingPage) {
    return (
      <div className="app-shell items-center justify-center bg-[var(--background)]">
        <div className="flex flex-col items-center gap-3">
          <span className="size-8 animate-spin rounded-full border-2 border-[var(--accent)] border-r-transparent" />
          <p className="text-sm text-[var(--ink-muted)]">
            Loading today&apos;s standup…
          </p>
        </div>
      </div>
    );
  }

  if (pageError) {
    return (
      <div className="app-shell items-center justify-center bg-[var(--background)] px-4">
        <div className="max-w-md rounded-lg border border-[var(--danger-border)] bg-white p-8 text-center shadow-sm">
          <h2 className="text-lg font-semibold text-[var(--ink)]">
            Couldn&apos;t load standup
          </h2>
          <p className="mt-2 text-sm text-[var(--ink-muted)]">{pageError}</p>
          <Button className="mt-5" onClick={() => void load()}>
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <AppHeader
        sessionDate={sessionDate}
        status={status}
        mockMode={mockMode}
        complete={complete}
        total={total}
      />

      <div className="app-body">
        <div className="app-forms">
          <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8 lg:py-7">
            <StandupForm
              drafts={drafts}
              onChange={onChange}
              onSave={onSave}
            />

            <div className="mt-6 lg:hidden">
              <SummaryPanel {...summaryProps} />
            </div>

            <p className="mt-10 pb-6 text-center text-[11px] text-[var(--ink-faint)]">
              Team Alpha · StandupBot ·{" "}
              {mockMode ? "Demo data" : "Connected to API"}
            </p>
          </div>
        </div>

        <div className="app-summary">
          <SummaryPanel {...summaryProps} docked />
        </div>
      </div>

      <Toast message={toast} tone={toastTone} />
    </div>
  );
}
