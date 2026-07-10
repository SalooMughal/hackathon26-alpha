"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  buildDraftsFromWorkspace,
  checkHealth,
  createSummary,
  getSummary,
  getTeam,
  getUpdates,
  isMockMode,
  loadStoredSummaryId,
  storeSummaryId,
  updateEntry,
} from "@/lib/api";
import {
  apiErrorToastMessage,
} from "@/lib/api-errors";
import { ApiError, type MemberDraft, type SummaryState } from "@/lib/types";
import {
  areAllEntriesComplete,
  completionCount,
  incompleteMemberNames,
  normalizeBlockers,
  savedReadyCount,
  validateEntry,
} from "@/lib/validation";
import { AppHeader } from "@/components/AppHeader";
import { StandupForm } from "@/components/StandupForm";
import { SummaryPanel } from "@/components/SummaryPanel";
import { Toast } from "@/components/Toast";
import { Button } from "@/components/Button";

export default function HomePage() {
  const [standupDate, setStandupDate] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<MemberDraft[]>([]);
  const [summary, setSummary] = useState<SummaryState | null>(null);
  const [mockMode, setMockMode] = useState(false);
  const [apiConnected, setApiConnected] = useState(false);
  const [dbOk, setDbOk] = useState(false);
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
      let healthOk = false;
      try {
        const health = await checkHealth();
        healthOk = health.status === "ok";
        setDbOk(health.db === "ok");
      } catch {
        healthOk = false;
        setDbOk(false);
      }

      const [team, updatesRes] = await Promise.all([
        getTeam(),
        getUpdates(),
      ]);

      const usingMock = isMockMode();
      setMockMode(usingMock);
      setApiConnected(healthOk && !usingMock);
      setStandupDate(updatesRes.standup_date);
      setDrafts(buildDraftsFromWorkspace(team, updatesRes.updates));

      if (!usingMock) {
        const storedId = loadStoredSummaryId(updatesRes.standup_date);
        if (storedId) {
          try {
            const existing = await getSummary(storedId);
            setSummary(existing);
          } catch {
            setSummary(null);
          }
        } else {
          setSummary(null);
        }
      } else {
        setSummary(null);
      }
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
      memberId: string,
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
    async (memberId: string) => {
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
        const blockers = normalizeBlockers(draft.blockers);
        const updated = await updateEntry(memberId, {
          yesterday: draft.yesterday.trim(),
          today: draft.today.trim(),
          blockers,
        });
        setDrafts((prev) =>
          prev.map((d) =>
            d.member_id === memberId
              ? {
                  ...d,
                  yesterday: updated.yesterday,
                  today: updated.today,
                  blockers: normalizeBlockers(updated.blockers),
                  dirty: false,
                  saving: false,
                  savedAt: updated.updated_at,
                  errors: {},
                }
              : d,
          ),
        );
        showToast(`Saved ${draft.member_name}'s update`);
      } catch (err) {
        if (err instanceof ApiError && err.code === "incomplete_update") {
          setDrafts((prev) =>
            prev.map((d) =>
              d.member_id === memberId
                ? {
                    ...d,
                    saving: false,
                    dirty: true,
                    errors: err.fieldErrors ?? {},
                  }
                : d,
            ),
          );
          showToast(apiErrorToastMessage(err.message), "error");
          return;
        }

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
    [drafts, showToast],
  );

  const persistAllDrafts = useCallback(
    async (entries: MemberDraft[]): Promise<MemberDraft[]> => {
      const saved: MemberDraft[] = [];
      for (const draft of entries) {
        const blockers = normalizeBlockers(draft.blockers);
        const updated = await updateEntry(draft.member_id, {
          yesterday: draft.yesterday.trim(),
          today: draft.today.trim(),
          blockers,
        });
        saved.push({
          ...draft,
          yesterday: updated.yesterday,
          today: updated.today,
          blockers: normalizeBlockers(updated.blockers),
          dirty: false,
          saving: false,
          savedAt: updated.updated_at,
          errors: {},
        });
      }
      return saved;
    },
    [],
  );

  const onGenerate = useCallback(async () => {
    const validated = drafts.map((d) => ({
      ...d,
      blockers: normalizeBlockers(d.blockers),
      errors: validateEntry({
        yesterday: d.yesterday,
        today: d.today,
        blockers: normalizeBlockers(d.blockers),
      }),
    }));
    setDrafts(validated);

    const missing = incompleteMemberNames(validated);
    if (!areAllEntriesComplete(validated)) {
      const detail =
        missing.length > 0
          ? `Still incomplete: ${missing.join(", ")}`
          : "Fill all fields for every teammate before summarizing.";
      setSummaryError(detail);
      showToast("Complete all teammate fields", "error");
      return;
    }

    setSummarizing(true);
    setSummaryError(null);

    try {
      const saved = await persistAllDrafts(validated);
      setDrafts(saved);

      const result = await createSummary(standupDate ?? undefined);
      setSummary(result);
      if (standupDate) {
        storeSummaryId(standupDate, result.summaryId);
      }
      showToast(
        summary ? "Summary regenerated" : "Summary generated",
        result.status === "degraded" ? "info" : "success",
      );
    } catch (err) {
      if (err instanceof ApiError && err.code === "incomplete_update" && err.memberId) {
        setDrafts((prev) =>
          prev.map((d) =>
            d.member_id === err.memberId
              ? {
                  ...d,
                  saving: false,
                  dirty: true,
                  errors: err.fieldErrors ?? {},
                }
              : d,
          ),
        );
        setSummaryError(apiErrorToastMessage(err.message));
        showToast(apiErrorToastMessage(err.message), "error");
        return;
      }

      const message =
        err instanceof ApiError
          ? err.message
          : "Failed to generate summary. Please try again.";
      setSummaryError(message);
      showToast(message, "error");
    } finally {
      setSummarizing(false);
    }
  }, [drafts, persistAllDrafts, standupDate, showToast, summary]);

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
  const hasUnsaved = drafts.some((d) => d.dirty);
  const { ready } = useMemo(() => savedReadyCount(drafts), [drafts]);
  const workspaceStatus = summary ? "summarized" : "draft";

  const summaryProps = {
    content: summary?.content ?? null,
    version: summary?.version ?? null,
    model: summary?.model ?? null,
    status: summary?.status ?? null,
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
        sessionDate={standupDate}
        status={workspaceStatus}
        mockMode={mockMode}
        apiConnected={apiConnected}
        dbOk={dbOk}
        complete={complete}
        total={total}
      />

      <div className="app-body">
        <div className="app-forms">
          <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8 lg:py-7">
            <StandupForm
              drafts={drafts}
              readyCount={ready}
              onChange={onChange}
              onSave={onSave}
            />

            <div className="mt-6 lg:hidden">
              <SummaryPanel {...summaryProps} />
            </div>

            <p className="mt-10 pb-6 text-center text-[11px] text-[var(--ink-faint)]">
              Team Alpha · StandupBot ·{" "}
              {mockMode
                ? "Demo mode"
                : apiConnected
                  ? dbOk
                    ? "API + DB connected"
                    : "API connected · DB unavailable"
                  : "API unreachable"}
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
