type BadgeTone = "neutral" | "success" | "warning" | "info" | "accent";

interface StatusBadgeProps {
  label: string;
  tone?: BadgeTone;
  pulse?: boolean;
}

const toneClasses: Record<BadgeTone, string> = {
  neutral:
    "bg-[var(--surface-muted)] text-[var(--ink-muted)] border-[var(--border)]",
  success: "bg-[var(--success-soft)] text-[var(--success)] border-[#ABF5D1]",
  warning: "bg-[var(--warning-soft)] text-[#974f0c] border-[#FFE2A8]",
  info: "bg-[var(--accent-soft)] text-[var(--accent)] border-[var(--accent-border)]",
  accent:
    "bg-[var(--accent-soft)] text-[var(--accent)] border-[var(--accent-border)]",
};

export function StatusBadge({
  label,
  tone = "neutral",
  pulse = false,
}: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded border px-2 py-0.5 text-[11px] font-semibold tracking-wide ${toneClasses[tone]}`}
    >
      {pulse ? (
        <span className="relative flex size-1.5">
          <span className="absolute inline-flex size-full animate-ping rounded-full bg-current opacity-40" />
          <span className="relative inline-flex size-1.5 rounded-full bg-current" />
        </span>
      ) : null}
      {label}
    </span>
  );
}
