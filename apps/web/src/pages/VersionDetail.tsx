import { useParams } from "react-router-dom";
import { useVersion } from "../lib/hooks";
import { Badge, Card, ErrorBox, Loading, Stat, fmt, fmtDate } from "../components/ui";
import { DocumentViewer } from "../components/DocumentViewer";
import { AuditLog } from "../components/AuditLog";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

const STATES = ["DRAFT", "VALIDATED", "PENDING_REVIEW", "APPROVED", "MONITORING", "RETIRED"];

export function VersionDetail() {
  const { id } = useParams();
  const q = useVersion(id);
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox error={q.error} />;
  const v = q.data!;
  const holdout = Object.fromEntries(v.metrics.filter((m) => m.scope === "holdout").map((m) => [m.metric_name, m]));
  const comp = Object.fromEntries(v.metrics.filter((m) => m.scope === "holdout_comparator").map((m) => [m.metric_name, m]));
  const importance = (v.artifacts.feature_importance ?? []) as any[];
  const reached = v.state === "REJECTED" ? ["DRAFT", "VALIDATED", "PENDING_REVIEW"] : STATES.slice(0, STATES.indexOf(v.state) + 1);
  const cfg = v.training_run.config_json ?? {};
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-semibold">{v.semantic_version}</h1>
        <Badge value={v.state} />
        <span className="muted text-sm">{v.model_type} · owner {v.owner}</span>
        <code className="faint text-xs">{v.id}</code>
      </div>
      <p className="muted text-sm">{v.narrative.intended_use ?? v.description ?? "Intended use not yet documented."}</p>

      <Card title="Lifecycle timeline">
        <ol className="flex flex-wrap gap-2 text-xs">
          {STATES.map((s) => (
            <li key={s} className="rounded-full border px-3 py-1" style={{ borderColor: reached.includes(s) ? "var(--series-1)" : "var(--border)", color: reached.includes(s) ? "var(--text-primary)" : "var(--text-muted)", fontWeight: s === v.state ? 600 : 400 }}>
              {s.replace("_", " ")}
            </li>
          ))}
          {v.state === "REJECTED" && <li className="rounded-full border px-3 py-1" style={{ borderColor: "var(--status-critical)", color: "var(--status-critical)" }}>REJECTED</li>}
        </ol>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Holdout AUC" value={fmt(holdout.auc?.metric_value)} sub={holdout.auc ? `95% CI ${fmt(holdout.auc.lower_ci)}–${fmt(holdout.auc.upper_ci)} · comparator ${fmt(comp.auc?.metric_value)}` : "run validation"} />
        <Stat label="KS" value={fmt(holdout.ks?.metric_value)} sub={holdout.ks ? `CI ${fmt(holdout.ks.lower_ci)}–${fmt(holdout.ks.upper_ci)}` : ""} />
        <Stat label="Brier" value={fmt(holdout.brier?.metric_value, 4)} sub={`comparator ${fmt(comp.brier?.metric_value, 4)}`} />
        <Stat label="ECE" value={fmt(holdout.ece?.metric_value, 4)} sub={`comparator ${fmt(comp.ece?.metric_value, 4)}`} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Lineage">
          <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-sm">
            <dt className="muted">Source</dt><dd>{v.source.name} <span className="faint">({v.source.id})</span></dd>
            <dt className="muted">License</dt><dd><a className="underline" href={v.source.license_url} target="_blank" rel="noreferrer">{v.source.license_name || v.source.license_url}</a> · retrieved {v.source.retrieval_date}</dd>
            <dt className="muted">Snapshot</dt><dd>{v.snapshot.as_of_date} · {v.snapshot.row_count.toLocaleString()} rows · <Badge value={v.snapshot.quality_status} label={`quality ${v.snapshot.quality_status}`} /></dd>
            <dt className="muted">Checksum</dt><dd><code className="text-xs">{v.snapshot.checksum}</code></dd>
            <dt className="muted">Training run</dt><dd><code className="text-xs">{v.training_run.id}</code> · seed {v.training_run.random_seed} · git {v.training_run.git_sha?.slice(0, 8) ?? "n/a"}</dd>
            <dt className="muted">Split</dt><dd>{cfg.split?.strategy} · train {cfg.split?.counts?.train} / val {cfg.split?.counts?.validation} / test {cfg.split?.counts?.test}</dd>
            <dt className="muted">Features</dt><dd className="text-xs">{(cfg.features ?? []).join(", ")}</dd>
            <dt className="muted">Excluded</dt><dd className="text-xs">{Object.keys(cfg.excluded_features ?? {}).join(", ")}</dd>
            <dt className="muted">Packages</dt><dd className="text-xs">{Object.entries(cfg.package_versions ?? {}).map(([k, val]) => `${k} ${val}`).join(" · ")}</dd>
            <dt className="muted">Registered</dt><dd>{fmtDate(v.created_at)}</dd>
          </dl>
        </Card>
        <Card title="Feature importance (permutation, AUC drop)">
          {importance.length === 0 ? (
            <p className="muted text-sm">Run validation to compute importance.</p>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={importance} layout="vertical" margin={{ left: 40, right: 16 }}>
                <CartesianGrid horizontal={false} stroke="var(--border)" />
                <XAxis type="number" tick={{ fontSize: 11 }} stroke="var(--text-muted)" />
                <YAxis type="category" dataKey="feature" width={130} tick={{ fontSize: 11 }} stroke="var(--text-muted)" />
                <Tooltip formatter={(x: number) => x.toFixed(4)} contentStyle={{ background: "var(--surface-1)", borderColor: "var(--border)" }} />
                <Bar dataKey="importance_mean" fill="var(--series-1)" radius={[0, 4, 4, 0]} barSize={14} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>
      </div>

      <Card title="Model card">
        <DocumentViewer versionId={v.semantic_version} type="model_card" />
      </Card>

      <Card title={`Audit log (${v.audit_events.length} events, hash-chained)`}>
        <AuditLog events={v.audit_events} />
      </Card>
    </div>
  );
}
