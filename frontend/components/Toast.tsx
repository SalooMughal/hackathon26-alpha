"use client";

interface ToastProps {
  message: string | null;
  tone?: "success" | "error" | "info";
}

export function Toast({ message, tone = "success" }: ToastProps) {
  if (!message) return null;

  const tones = {
    success: "bg-[#064E3B] text-white",
    error: "bg-[#7F1D1D] text-white",
    info: "bg-[#0F172A] text-white",
  };

  return (
    <div
      role="status"
      className={`fixed bottom-6 left-1/2 z-50 -translate-x-1/2 animate-slide-up rounded-xl px-4 py-2.5 text-sm font-medium shadow-lg ${tones[tone]}`}
    >
      {message}
    </div>
  );
}
