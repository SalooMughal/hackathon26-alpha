"use client";

import type { MemberDraft } from "@/lib/types";
import { MemberCard } from "./MemberCard";

interface StandupFormProps {
  drafts: MemberDraft[];
  onChange: (
    memberId: number,
    field: "yesterday" | "today" | "blockers",
    value: string,
  ) => void;
  onSave: (memberId: number) => void;
}

export function StandupForm({ drafts, onChange, onSave }: StandupFormProps) {
  const ready = drafts.filter(
    (d) =>
      d.yesterday.trim() &&
      d.today.trim() &&
      d.blockers.trim() &&
      !d.dirty,
  ).length;

  return (
    <section className="flex flex-col gap-5" aria-label="Team standup forms">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.12em] text-[var(--accent)]">
            Daily standup
          </p>
          <h2 className="mt-1 text-xl font-bold tracking-tight text-[var(--ink)] sm:text-2xl">
            Team updates
          </h2>
          <p className="mt-1 max-w-lg text-[14px] text-[var(--ink-muted)]">
            Each teammate fills Yesterday, Today, and Blockers — then generate
            one Slack-ready summary.
          </p>
        </div>
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3.5 py-2 shadow-sm">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-[var(--ink-faint)]">
            Saved & ready
          </p>
          <p className="text-lg font-bold tabular-nums text-[var(--ink)]">
            {ready}
            <span className="text-sm font-medium text-[var(--ink-faint)]">
              /{drafts.length}
            </span>
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-4 pb-4">
        {drafts.map((draft, index) => (
          <MemberCard
            key={draft.member_id}
            draft={draft}
            index={index}
            onChange={onChange}
            onSave={onSave}
          />
        ))}
      </div>
    </section>
  );
}
