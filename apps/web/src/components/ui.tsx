import type { ReactNode } from "react";

const STATE_TONE: Record<string, string> = {
  DRAFT: "neutral", VALIDATED: "neutral", PENDING_REVIEW: "warning", APPROVED: "good", MONITORING: "good", REJECTED: "critical", RETIRED: "neutral",
  pass: "good", fail: "critical", ok: "good", investigate: "warning", alert: "critical", failed: "critical",
  open: "serious", investigating: "warning", resolved: "good", high: "critical", medium: "warning", low: "neutral",
  complete: "good", draft: "warning", healthy: "good", watch: "warning", at_risk: "critical", retired: "neutral", stable: "good",
  approve: "good", reject: "critical", COMPLETED: "good", FAILED: "critical", RUNNING: "warning", QUEUED: "neutral",
};
const TONE_ICON: Record<string, string> = { good: "●", warning: "▲", serious: "▲", critical: "■", neutral: "○" };

/** Status pill: colour + icon + text label, never colour alone. */
export function Badge({ value, label }: { value: string; label?: string }) {
  const tone = STATE_TONE[value] ?? "neutral";
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium"
      style={{ color: `var(--status-${tone})`, borderColor: `var(--status-${tone})` }}
      data-tone={tone}
    >
      <span aria-hidden>{TONE_ICON[tone]}</span>
      {label ?? value.replace(/_/g, " ")}
    </span>
  );
}

export function Card({ title, children, actions, className = "" }: { title?: ReactNode; children: ReactNode; actions?: ReactNode; className?: string }) {
  return (
    <section className={`card ${className}`}>
      {(title || actions) && (
        <header className="mb-3 flex items-center justify-between gap-2">
          {title && <h2 className="text-sm font-semibold">{title}</h2>}
          {actions}
        </header>
      )}
      {children}
    </section>
  );
}

export function Stat({ label, value, sub }: { label: string; value: ReactNode; sub?: ReactNode }) {
  return (
    <div className="card">
      <div className="faint text-xs uppercase tracking-wide">{label}</div>
      <div className="mt-1 text-2xl font-semibold tabular-nums">{value}</div>
      {sub && <div className="muted mt-1 text-xs">{sub}</div>}
    </div>
  );
}

export const fmt = (x: number | null | undefined, d = 3) => (x === null || x === undefined || Number.isNaN(x) ? "—" : x.toFixed(d));
export const fmtDate = (s: string) => new Date(s).toLocaleString();

export function Loading() {
  return <div className="muted p-6 text-sm">Loading…</div>;
}
export function ErrorBox({ error }: { error: any }) {
  const p = error?.problem;
  return (
    <div className="card border-[var(--status-critical)]">
      <div className="text-sm font-semibold" style={{ color: "var(--status-critical)" }}>
        {p?.title ?? "Error"} {p?.status ? `(${p.status})` : ""}
      </div>
      <div className="muted mt-1 text-sm">{p?.detail ?? String(error?.message ?? error)}</div>
      {p?.blocking && (
        <ul className="mt-2 list-disc pl-5 text-sm">
          {p.blocking.map((b: any) => (
            <li key={b.check_name}>
              <strong>{b.check_name.replace(/_/g, " ")}</strong>: {b.missing.join("; ")}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
