import type { ReactNode } from "react";
import { GLOSSARY, HEALTH_LABEL, STATE_LABEL, type GlossaryKey } from "../lib/glossary";

const TONE: Record<string, string> = {
  DRAFT: "neutral", VALIDATED: "neutral", PENDING_REVIEW: "warning", APPROVED: "good", MONITORING: "good", REJECTED: "critical", RETIRED: "neutral",
  pass: "good", fail: "critical", ok: "good", investigate: "warning", alert: "critical", failed: "critical",
  open: "serious", investigating: "warning", resolved: "good", high: "critical", medium: "warning", low: "neutral",
  complete: "good", draft: "warning", healthy: "good", watch: "warning", at_risk: "critical", retired: "neutral", stable: "good",
  approve: "good", reject: "critical", COMPLETED: "good", FAILED: "critical", RUNNING: "warning", QUEUED: "neutral",
};
const LABEL: Record<string, string> = {
  ...STATE_LABEL,
  ...HEALTH_LABEL,
  pass: "Meets requirement", fail: "Missing evidence", ok: "Stable", investigate: "Investigate", alert: "Alert", failed: "Failed",
  open: "Open", investigating: "Investigating", resolved: "Resolved", high: "High", medium: "Medium", low: "Low",
  complete: "Complete", draft: "Draft", stable: "Stable", approve: "Approved", reject: "Rejected",
};

/** Status pill: tinted background + text label, never colour alone. */
export function Badge({ value, label }: { value: string; label?: string }) {
  const tone = TONE[value] ?? "neutral";
  return (
    <span
      className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium"
      style={{ color: `var(--${tone})`, background: `var(--${tone}-bg)` }}
      data-tone={tone}
    >
      <span aria-hidden className="inline-block h-1.5 w-1.5 rounded-full" style={{ background: `var(--${tone})` }} />
      {label ?? LABEL[value] ?? value.replace(/_/g, " ")}
    </span>
  );
}

/** Plain label with its technical name alongside; hover shows the short explanation, the page glossary has the full one. */
export function Term({ k, children, hideAbbr = false }: { k: GlossaryKey; children?: ReactNode; hideAbbr?: boolean }) {
  const g = GLOSSARY[k];
  return (
    <abbr className="term" title={`${g.jargon} (${g.abbr}). ${g.short}`}>
      {children ?? g.plain}
      {!hideAbbr && <span className="faint font-normal"> · {g.abbr}</span>}
    </abbr>
  );
}

/** Collapsible glossary: for each term, the technical name, what it computes, the plain meaning, and how the two connect. */
export function Glossary({ keys }: { keys: GlossaryKey[] }) {
  return (
    <details className="glossary card">
      <summary>Plain language and the technical terms behind it</summary>
      <p className="muted mt-2 text-sm">Each label on this page is shown in everyday words with the technical term beside it. Here is what each term computes and how the two map onto each other.</p>
      <dl className="mt-4 space-y-5">
        {keys.map((k) => {
          const g = GLOSSARY[k];
          return (
            <div key={k} className="border-t pt-4 hairline">
              <dt className="text-sm">
                <span className="font-semibold">{g.plain}</span>
                <span className="muted"> — {g.jargon}{g.abbr !== g.plain ? ` (${g.abbr})` : ""}</span>
              </dt>
              <dd className="mt-2 grid gap-3 text-sm md:grid-cols-3">
                <div><div className="faint text-xs uppercase tracking-wide">In plain terms</div><div className="mt-1">{g.short}</div></div>
                <div><div className="faint text-xs uppercase tracking-wide">What is computed</div><div className="muted mt-1">{g.technical}</div></div>
                <div><div className="faint text-xs uppercase tracking-wide">How they connect</div><div className="muted mt-1">{g.bridge}</div></div>
              </dd>
            </div>
          );
        })}
      </dl>
    </details>
  );
}

export function Card({ title, subtitle, children, actions, className = "" }: { title?: ReactNode; subtitle?: ReactNode; children: ReactNode; actions?: ReactNode; className?: string }) {
  return (
    <section className={`card ${className}`}>
      {(title || actions) && (
        <header className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <div>
            {title && <h2>{title}</h2>}
            {subtitle && <p className="muted mt-0.5 text-sm">{subtitle}</p>}
          </div>
          {actions}
        </header>
      )}
      {children}
    </section>
  );
}

/** Big number with a plain-language reading underneath. */
export function Stat({ label, value, reading, term }: { label: string; value: ReactNode; reading?: ReactNode; term?: GlossaryKey }) {
  return (
    <div className="card">
      <div className="muted text-sm">{term ? <Term k={term}>{label}</Term> : label}</div>
      <div className="tabular mt-1 text-[28px] font-semibold leading-none tracking-tight">{value}</div>
      {reading && <div className="faint mt-2 text-[13px] leading-snug">{reading}</div>}
    </div>
  );
}

export function PageHeader({ title, lede, badges }: { title: ReactNode; lede?: ReactNode; badges?: ReactNode }) {
  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <h1>{title}</h1>
        {badges}
      </div>
      {lede && <p className="muted mt-2 max-w-3xl text-[15px]">{lede}</p>}
    </div>
  );
}

export const fmt = (x: number | null | undefined, d = 3) => (x === null || x === undefined || Number.isNaN(x) ? "—" : x.toFixed(d));
export const pct = (x: number | null | undefined, d = 0) => (x === null || x === undefined || Number.isNaN(x) ? "—" : `${(x * 100).toFixed(d)}%`);
export const fmtDate = (s: string) => new Date(s).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });

export function Loading() {
  return <div className="muted p-6 text-sm">Loading…</div>;
}

export function ErrorBox({ error }: { error: any }) {
  const p = error?.problem;
  return (
    <div className="card" style={{ borderColor: "var(--critical)" }} role="alert">
      <div className="text-sm font-semibold" style={{ color: "var(--critical)" }}>
        {p?.title ?? "Something went wrong"}
      </div>
      <div className="muted mt-1 text-sm">{p?.detail ?? String(error?.message ?? error)}</div>
      {p?.blocking && (
        <ul className="mt-3 space-y-2 text-sm">
          {p.blocking.map((b: any) => (
            <li key={b.check_name}>
              <div className="font-medium">{b.check_name.replace(/_/g, " ")}</div>
              <ul className="muted list-disc pl-5">
                {b.missing.map((m: string) => (
                  <li key={m}>{m}</li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
