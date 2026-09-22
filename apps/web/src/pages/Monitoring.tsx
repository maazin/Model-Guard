import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useParams } from "react-router-dom";
import { useMonitoring } from "../lib/hooks";
import { patch } from "../lib/api";
import type { Alert } from "../lib/types";
import { Badge, Card, ErrorBox, Loading, fmt } from "../components/ui";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine, Legend } from "recharts";

const tip = { contentStyle: { background: "var(--surface-1)", borderColor: "var(--border)", fontSize: 12 } };

function AlertRow({ a, versionId }: { a: Alert; versionId: string }) {
  const qc = useQueryClient();
  const [note, setNote] = useState("");
  const [err, setErr] = useState<any>(null);
  const m = useMutation({
    mutationFn: (status: string) => patch(`/api/v1/model-versions/${versionId}/alerts/${a.id}`, { status, note }),
    onSuccess: () => { setNote(""); setErr(null); qc.invalidateQueries({ queryKey: ["monitoring", versionId] }); },
    onError: setErr,
  });
  return (
    <tr data-testid="alert-row">
      <td><Badge value={a.severity} /></td>
      <td>{a.title}<div className="faint text-xs">{a.type} · owner {a.owner} · due {a.due_date}</div>{a.investigation_note && <div className="muted text-xs">Investigation: {a.investigation_note}</div>}{a.resolution_note && <div className="muted text-xs">Resolution: {a.resolution_note}</div>}</td>
      <td><Badge value={a.status} /></td>
      <td>
        {a.status !== "resolved" && (
          <div className="flex flex-col gap-1">
            <input className="btn text-xs" placeholder="Note (required to resolve)" value={note} onChange={(e) => setNote(e.target.value)} aria-label={`Note for ${a.title}`} />
            <div className="flex gap-1">
              {a.status === "open" && <button className="btn text-xs" onClick={() => m.mutate("investigating")} disabled={m.isPending}>Investigate</button>}
              <button className="btn btn-primary text-xs" onClick={() => m.mutate("resolved")} disabled={m.isPending || !note}>Resolve</button>
            </div>
            {err && <span className="text-xs" style={{ color: "var(--status-critical)" }}>{err.problem?.detail ?? "error"}</span>}
          </div>
        )}
      </td>
    </tr>
  );
}

export function Monitoring() {
  const { id } = useParams();
  const q = useMonitoring(id);
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox error={q.error} />;
  const mon = q.data!;
  const batches = mon.batches;
  const features = batches.length ? Object.keys(batches[0].results_json.psi ?? {}) : [];
  const trend = batches.map((b) => ({
    date: b.as_of_date,
    auc: b.results_json.performance?.auc?.value ?? null,
    auc_lo: b.results_json.performance?.auc?.lower_ci ?? null,
    auc_hi: b.results_json.performance?.auc?.upper_ci ?? null,
    score_psi: b.results_json.score_drift?.psi ?? null,
    max_psi: Math.max(0, ...Object.values(b.results_json.psi ?? {}).map((x: any) => x.psi)),
    null_rate: Math.max(0, ...Object.values(b.results_json.data_quality?.null_rates ?? {}).map((x: any) => Number(x))),
    dup_rate: b.results_json.data_quality?.duplicate_rate ?? 0,
    default_rate: b.results_json.performance?.observed_default_rate?.value ?? null,
  }));
  const open = mon.alerts.filter((a) => a.status !== "resolved");
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-semibold">Monitoring · {mon.model_version}</h1>
        <Badge value={mon.state} />
        <span className="faint text-xs">PSI defaults: stable &lt; {mon.thresholds.psi_investigate}, investigate {mon.thresholds.psi_investigate}–{mon.thresholds.psi_alert}, alert &gt; {mon.thresholds.psi_alert} (configurable project defaults, not regulatory thresholds)</span>
      </div>
      {batches.length === 0 && <Card title="No batches yet"><p className="muted text-sm">Monitoring runs for an APPROVED model on a dated snapshot imported with purpose "monitoring". Use <code>POST /api/v1/model-versions/{'{id}'}/monitoring-batches</code> or <code>make seed</code>.</p></Card>}
      {batches.length > 0 && (
        <>
          <div className="grid gap-4 lg:grid-cols-3">
            <Card title="Performance trend (AUC, labelled batches)">
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={trend} margin={{ left: 0, right: 12, top: 8 }}>
                  <CartesianGrid stroke="var(--border)" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="var(--text-muted)" />
                  <YAxis domain={[0.5, 1]} tick={{ fontSize: 11 }} stroke="var(--text-muted)" />
                  <Tooltip {...tip} formatter={(x: number) => (x === null ? "n/a" : x.toFixed(3))} />
                  {mon.holdout_auc && <ReferenceLine y={mon.holdout_auc} stroke="var(--series-2)" strokeDasharray="4 4" label={{ value: "holdout", fontSize: 10, fill: "var(--text-secondary)" }} />}
                  <Line dataKey="auc" stroke="var(--series-1)" strokeWidth={2} dot={{ r: 4 }} connectNulls isAnimationActive={false} name="batch AUC" />
                </LineChart>
              </ResponsiveContainer>
            </Card>
            <Card title="Drift trend (PSI)">
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={trend} margin={{ left: 0, right: 12, top: 8 }}>
                  <CartesianGrid stroke="var(--border)" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="var(--text-muted)" />
                  <YAxis tick={{ fontSize: 11 }} stroke="var(--text-muted)" />
                  <Tooltip {...tip} formatter={(x: number) => x.toFixed(3)} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <ReferenceLine y={mon.thresholds.psi_alert} stroke="var(--status-critical)" strokeDasharray="4 4" />
                  <ReferenceLine y={mon.thresholds.psi_investigate} stroke="var(--status-warning)" strokeDasharray="4 4" />
                  <Line dataKey="max_psi" stroke="var(--series-1)" strokeWidth={2} dot={{ r: 4 }} isAnimationActive={false} name="max feature PSI" />
                  <Line dataKey="score_psi" stroke="var(--series-2)" strokeWidth={2} dot={{ r: 4 }} isAnimationActive={false} name="score PSI" />
                </LineChart>
              </ResponsiveContainer>
            </Card>
            <Card title="Data-quality trend">
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={trend} margin={{ left: 0, right: 12, top: 8 }}>
                  <CartesianGrid stroke="var(--border)" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="var(--text-muted)" />
                  <YAxis tick={{ fontSize: 11 }} stroke="var(--text-muted)" tickFormatter={(x) => `${(x * 100).toFixed(0)}%`} />
                  <Tooltip {...tip} formatter={(x: number) => `${(x * 100).toFixed(2)}%`} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line dataKey="null_rate" stroke="var(--series-1)" strokeWidth={2} dot={{ r: 4 }} isAnimationActive={false} name="max null rate" />
                  <Line dataKey="dup_rate" stroke="var(--series-2)" strokeWidth={2} dot={{ r: 4 }} isAnimationActive={false} name="duplicate rate" />
                  <Line dataKey="default_rate" stroke="var(--series-3)" strokeWidth={2} dot={{ r: 4 }} isAnimationActive={false} name="observed default rate" connectNulls />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          </div>
          <Card title="PSI by feature and batch">
            <div className="overflow-auto">
              <table className="data" data-testid="psi-table">
                <thead><tr><th>Feature</th>{batches.map((b) => <th key={b.id}>{b.as_of_date}</th>)}</tr></thead>
                <tbody>
                  {features.map((f) => (
                    <tr key={f}>
                      <td><code>{f}</code></td>
                      {batches.map((b) => { const r = b.results_json.psi[f]; return <td key={b.id} className="tabular-nums"><span className="mr-2">{fmt(r.psi)}</span><Badge value={r.status} /></td>; })}
                    </tr>
                  ))}
                  <tr><td><em>prediction score</em></td>{batches.map((b) => <td key={b.id} className="tabular-nums"><span className="mr-2">{fmt(b.results_json.score_drift?.psi)}</span><Badge value={b.results_json.score_drift?.status ?? "stable"} /></td>)}</tr>
                  <tr><td>batch status</td>{batches.map((b) => <td key={b.id}><Badge value={b.status} /> {b.labels_available ? <span className="faint text-xs">labels</span> : <span className="faint text-xs">no labels</span>}</td>)}</tr>
                  <tr><td>KS test (worst feature)</td>{batches.map((b) => { const h = b.results_json.hypothesis_test; return <td key={b.id} className="text-xs">{h ? <><code>{h.feature}</code> D={fmt(h.statistic)} p={h.p_value.toExponential(1)}</> : "—"}</td>; })}</tr>
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
      <Card title={`Alerts (${open.length} open, ${mon.alerts.length - open.length} resolved)`}>
        {mon.alerts.length === 0 ? <p className="muted text-sm">No alerts.</p> : (
          <table className="data">
            <thead><tr><th>Severity</th><th>Alert</th><th>Status</th><th>Action</th></tr></thead>
            <tbody>{[...mon.alerts].sort((a, b) => (a.status === "resolved" ? 1 : 0) - (b.status === "resolved" ? 1 : 0)).map((a) => <AlertRow key={a.id} a={a} versionId={mon.model_version} />)}</tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
