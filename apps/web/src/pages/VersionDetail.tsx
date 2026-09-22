import { useParams } from "react-router-dom";
import { useVersion } from "../lib/hooks";
import { Badge, Card, ErrorBox, Glossary, Loading, PageHeader, Stat, Term, fmt, fmtDate } from "../components/ui";
import { DocumentViewer } from "../components/DocumentViewer";
import { AuditLog } from "../components/AuditLog";
import { STATE_LABEL } from "../lib/glossary";
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
  const otherName = v.model_type === "champion" ? "the simpler reference model" : "the gradient-boosted candidate";
  return (
    <div className="space-y-8">
      <PageHeader
        title={v.semantic_version}
        lede={v.narrative.intended_use ?? v.description ?? "Intended use not yet documented."}
        badges={<Badge value={v.state} />}
      />

      <Card title={<>Where this version is in its life <span className="faint font-normal">· lifecycle state</span></>} subtitle={<Term k="lifecycle">Each step is recorded in the audit log below.</Term>}>
        <ol className="flex flex-wrap gap-2">
          {STATES.map((s) => (
            <li key={s} className="rounded-full border px-3 py-1 text-sm" style={{ borderColor: reached.includes(s) ? "var(--accent)" : "var(--hairline)", color: reached.includes(s) ? "var(--text)" : "var(--text-3)", fontWeight: s === v.state ? 600 : 400 }}>
              {STATE_LABEL[s]}
            </li>
          ))}
          {v.state === "REJECTED" && <li className="rounded-full border px-3 py-1 text-sm" style={{ borderColor: "var(--critical)", color: "var(--critical)" }}>Rejected</li>}
        </ol>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Ranking accuracy" term="auc" value={fmt(holdout.auc?.metric_value)} reading={holdout.auc ? `Likely between ${fmt(holdout.auc.lower_ci)} and ${fmt(holdout.auc.upper_ci)}; ${otherName} scores ${fmt(comp.auc?.metric_value)}.` : "Run validation to measure."} />
        <Stat label="Separation" term="ks" value={fmt(holdout.ks?.metric_value)} reading={holdout.ks ? `Likely between ${fmt(holdout.ks.lower_ci)} and ${fmt(holdout.ks.upper_ci)}.` : ""} />
        <Stat label="Forecast error" term="brier" value={fmt(holdout.brier?.metric_value, 4)} reading={`Lower is better; ${otherName}: ${fmt(comp.brier?.metric_value, 4)}.`} />
        <Stat label="Calibration error" term="ece" value={fmt(holdout.ece?.metric_value, 4)} reading={`Lower is better; ${otherName}: ${fmt(comp.ece?.metric_value, 4)}.`} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title={<>Where the data came from <span className="faint font-normal">· lineage</span></>} subtitle={<Term k="lineage">Everything needed to reproduce this version.</Term>}>
          <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
            <dt className="muted">Dataset</dt><dd>{v.source.name} <span className="faint">({v.source.id})</span></dd>
            <dt className="muted">Licence</dt><dd><a className="underline" href={v.source.license_url} target="_blank" rel="noreferrer">{v.source.license_name || v.source.license_url}</a>, retrieved {v.source.retrieval_date}</dd>
            <dt className="muted">Snapshot</dt><dd>{v.snapshot.row_count.toLocaleString()} records as of {v.snapshot.as_of_date} · <Badge value={v.snapshot.quality_status} label={`data quality: ${v.snapshot.quality_status}`} /></dd>
            <dt className="muted"><Term k="checksum">Checksum</Term></dt><dd><code className="break-all text-xs">{v.snapshot.checksum}</code></dd>
            <dt className="muted">Training run</dt><dd><code className="text-xs">{v.training_run.id.slice(0, 8)}</code> · seed {v.training_run.random_seed} · code version {v.training_run.git_sha?.slice(0, 8) ?? "n/a"}</dd>
            <dt className="muted"><Term k="holdout">Data split</Term></dt><dd>{cfg.split?.strategy === "temporal" ? "By time: the most recent records are held out for testing" : "Random, stratified split (the data has no dates)"} · train {cfg.split?.counts?.train?.toLocaleString()} / validate {cfg.split?.counts?.validation?.toLocaleString()} / test {cfg.split?.counts?.test?.toLocaleString()}</dd>
            <dt className="muted">Inputs used</dt><dd className="text-xs">{(cfg.features ?? []).join(", ")}</dd>
            <dt className="muted">Deliberately excluded</dt><dd className="text-xs">{Object.entries(cfg.excluded_features ?? {}).map(([k, why]) => <div key={k}><strong>{k}</strong> — {String(why)}</div>)}</dd>
            <dt className="muted">Registered</dt><dd>{fmtDate(v.created_at)} by {v.owner.replace(/_/g, " ")}</dd>
          </dl>
        </Card>
        <Card title={<>Which inputs matter most <span className="faint font-normal">· permutation importance</span></>} subtitle={<Term k="importance">Drop in ranking accuracy when each input is scrambled.</Term>}>
          {importance.length === 0 ? (
            <p className="muted text-sm">Run validation to compute importance.</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={importance} layout="vertical" margin={{ left: 24, right: 16 }}>
                <CartesianGrid horizontal={false} stroke="var(--hairline)" />
                <XAxis type="number" tick={{ fontSize: 11, fill: "var(--text-3)" }} stroke="var(--hairline)" />
                <YAxis type="category" dataKey="feature" width={150} tick={{ fontSize: 11, fill: "var(--text-2)" }} stroke="var(--hairline)" />
                <Tooltip formatter={(x: number) => x.toFixed(4)} contentStyle={{ background: "var(--surface)", borderColor: "var(--hairline)", borderRadius: 10, fontSize: 12 }} />
                <Bar dataKey="importance_mean" fill="var(--series-1)" radius={[0, 4, 4, 0]} barSize={14} name="importance" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>
      </div>

      <Card title="Model card" subtitle={<Term k="modelCard">The full written record for this version.</Term>}>
        <DocumentViewer versionId={v.semantic_version} type="model_card" />
      </Card>

      <Card title={<>Permanent record of changes <span className="faint font-normal">· hash-chained audit log</span></>} subtitle={<Term k="audit">{v.audit_events.length} events, newest first. Each carries a fingerprint chained to the previous one.</Term>}>
        <AuditLog events={v.audit_events} />
      </Card>
      <Glossary keys={["auc", "ks", "brier", "ece", "ci", "holdout", "lineage", "checksum", "importance", "modelCard", "audit"]} />
    </div>
  );
}
