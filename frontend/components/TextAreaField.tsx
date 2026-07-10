import { type ReactNode, type TextareaHTMLAttributes } from "react";

interface TextAreaFieldProps
  extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  hint?: string;
  error?: string;
  icon?: ReactNode;
  charCount?: number;
  maxChars?: number;
}

export function TextAreaField({
  label,
  hint,
  error,
  icon,
  charCount,
  maxChars = 500,
  id,
  className = "",
  rows = 3,
  ...props
}: TextAreaFieldProps) {
  const fieldId = id ?? label.toLowerCase().replace(/\s+/g, "-");

  return (
    <label className="flex h-full flex-col gap-2" htmlFor={fieldId}>
      <span className="flex items-center justify-between gap-2">
        <span className="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-[0.06em] text-[var(--ink-muted)]">
          {icon ? (
            <span className="text-[var(--accent)] opacity-80">{icon}</span>
          ) : null}
          {label}
        </span>
        {typeof charCount === "number" ? (
          <span
            className={`text-[10px] tabular-nums ${
              charCount > maxChars
                ? "text-[var(--danger)]"
                : "text-[var(--ink-faint)]"
            }`}
          >
            {charCount}/{maxChars}
          </span>
        ) : null}
      </span>
      <textarea
        id={fieldId}
        rows={rows}
        className={`min-h-[112px] w-full flex-1 resize-y rounded-lg border bg-white/90 px-3 py-2.5 text-[13.5px] leading-relaxed text-[var(--ink)] shadow-[inset_0_1px_2px_rgba(11,31,51,0.03)] transition-all placeholder:text-[var(--ink-faint)] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/20 ${
          error
            ? "border-[var(--danger-border)] focus:border-[var(--danger)]"
            : "border-white/80 hover:border-[var(--border)] focus:border-[var(--accent)]"
        } ${className}`}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${fieldId}-error` : undefined}
        {...props}
      />
      {error ? (
        <span
          id={`${fieldId}-error`}
          className="text-xs font-medium text-[var(--danger)]"
        >
          {error}
        </span>
      ) : hint ? (
        <span className="text-[11px] text-[var(--ink-faint)]">{hint}</span>
      ) : null}
    </label>
  );
}
