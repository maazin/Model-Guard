import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useParams } from "react-router-dom";
import { useMonitoring } from "../lib/hooks";
import { patch } from "../lib/api";
import type { Alert } from "../lib/types";
import { Badge, Card, ErrorBox, Glossary, Loading, PageHeader, Term, fmt } from "../components/ui";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine, Legend } from "recharts";

const tip = { contentStyle: { background: "var(--surface)", borderColor: "var(--hairline)", borderRadius: 10, fontSize: 12 } };
const axis = { fontSize: 11, fill: "var(--text-3)" };
const TYPE_LABEL: Record<string, string> = { data_quality: "Data quality", psi: "Population shift", score_drift: "Score drift", performance: "Accuracy", fairness: "Fairness" };

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
      <td>
        <div>{a.title}</div>
        <div className="faint text-xs">{TYPE_LABEL[a.type] ?? a.type} · owner {a.owner.replace(/_/g, " ")} · due {a.due_date}</div>
        {a.investigation_note && <div className="muted mt-1 text-xs">Investigation: {a.investigation_note}</div>}
        {a.resolution_note && <div className="muted mt-1 text-xs">Resolution: {a.resolution_note}</div>}
      </td>
      <td><Badge value={a.status} /></td>
      <td>
        {a.status !== "resolved" && (
          <div className="flex flex-col gap-1.5">
            <input className="field" placeholder="Add a note (required to resolve)" value={note} onChange={(e) => setNote(e.target.value)} aria-label={`Note for ${a.title}`} />
            <div className="flex gap-1.5">
              {a.status === "open" && <button className="btn" onClick={() => m.mutate("investigating")} disabled={m.isPending}>Start investigating</button>}
              <button className="btn btn-primary" onClick={() => m.mutate("resolved")} disabled={m.isPending || !note}>Resolve</button>
            </div>
            {err && <span className="text-xs" style={{ color: "var(--critical)" }}>{err.problem?.detail ?? "Could not update the alert."}</span>}
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
    score_psi: b.results_json.score_drift?.psi ?? null,
    max_psi: Math.max(0, ...Object.values(b.results_json.psi ?? {}).map((x: any) => x.psi)),
    null_rate: Math.max(0, ...Object.values(b.results_json.data_quality?.null_rates ?? {}).map((x: any) => Number(x))),
    dup_rate: b.results_json.data_quality?.duplicate_rate ?? 0,
    default_rate: b.results_json.performance?.observed_default_rate?.value ?? null,
  }));
  const open = mon.alerts.filter((a) => a.status !== "resolved");
  const latest = batches[batches.length - 1];
  const lede = batches.length === 0
    ? "Once a version is approved, each new batch of borrowers it scores is checked here for data problems, shifts in the population and falling accuracy."
    : `${batches.length} dated batches have been checked. The latest (${latest.as_of_date}) is rated “${latest.status}”; ${open.length} alert${open.length === 1 ? "" : "s"} ${open.length === 1 ? "is" : "are"} open.`;
  return (
    <div className="space-y-8">
      <PageHeader title="Monitoring" lede={lede} badges={<Badge value={mon.state} />} />
      {batches.length === 0 && <Card title="No batches yet"><p className="muted text-sm">Monitoring runs for an approved model on a dated batch of new records.</p></Card>}
      {batches.length > 0 && (
        <>
          <div className="grid gap-4 lg:grid-cols-3">
            <Card title="Is accuracy holding up?" subtitle="Ranking accuracy on each batch where outcomes are known; dotted line is the level at approval.">
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={trend} margin={{ left: 0, right: 12, top: 8 }}>
                  <CartesianGrid stroke="var(--hairline)" />
                  <XAxis dataKey="date" tick={axis} stroke="var(--hairline)" />
                  <YAxis domain={[0.5, 1]} tick={axis} stroke="var(--hairline)" />
                  <Tooltip {...tip} formatter={(x: number) => (x === null ? "n/a" : x.toFixed(3))} />
                  {mon.holdout_auc && <ReferenceLine y={mon.holdout_auc} stroke="var(--series-2)" strokeDasharray="4 4" />}
                  <Line dataKey="auc" stroke="var(--series-1)" strokeWidth={2} dot={{ r: 4 }} connectNulls isAnimationActive={false} name="ranking accuracy" />
                </LineChart>
              </ResponsiveContainer>
            </Card>
            <Card title="Are the borrowers changing?" subtitle={<><Term k="psi">Population shift</Term> of the most-changed input and of the scores. Dotted lines: investigate / alert.</>}>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={trend} margin={{ left: 0, right: 12, top: 8 }}>
                  <CartesianGrid stroke="var(--hairline)" />
                  <XAxis dataKey="date" tick={axis} stroke="var(--hairline)" />
                  <YAxis tick={axis} stroke="var(--hairline)" />
                  <Tooltip {...tip} formatter={(x: number) => x.toFixed(3)} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <ReferenceLine y={mon.thresholds.psi_alert} stroke="var(--critical)" strokeDasharray="4 4" />
                  <ReferenceLine y={mon.thresholds.psi_investigate} stroke="var(--warning)" strokeDasharray="4 4" />
                  <Line dataKey="max_psi" stroke="var(--series-1)" strokeWidth={2} dot={{ r: 4 }} isAnimationActive={false} name="largest input shift" />
                  <Line dataKey="score_psi" stroke="var(--series-2)" strokeWidth={2} dot={{ r: 4 }} isAnimationActive={false} name="score shift" />
                </LineChart>
              </ResponsiveContainer>
            </Card>
            <Card title="Is the data clean?" subtitle="Missing values, duplicates and the share of borrowers who actually defaulted.">
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={trend} margin={{ left: 0, right: 12, top: 8 }}>
                  <CartesianGrid stroke="var(--hairline)" />
                  <XAxis dataKey="date" tick={axis} stroke="var(--hairline)" />
                  <YAxis tick={axis} stroke="var(--hairline)" tickFormatter={(x) => `${(x * 100).toFixed(0)}%`} />
                  <Tooltip {...tip} formatter={(x: number) => `${(x * 100).toFixed(2)}%`} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Line dataKey="null_rate" stroke="var(--series-1)" strokeWidth={2} dot={{ r: 4 }} isAnimationActive={false} name="missing values" />
                  <Line dataKey="dup_rate" stroke="var(--series-2)" strokeWidth={2} dot={{ r: 4 }} isAnimationActive={false} name="duplicates" />
                  <Line dataKey="default_rate" stroke="var(--series-3)" strokeWidth={2} dot={{ r: 4 }} isAnimationActive={false} name="actual default rate" connectNulls />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          </div>
          <Card title="Shift in each input, batch by batch" subtitle={<>Project defaults: below {mon.thresholds.psi_investigate} stable, {mon.thresholds.psi_investigate}–{mon.thresholds.psi_alert} investigate, above {mon.thresholds.psi_alert} alert. These are configurable, not regulatory.</>}>
            <div className="overflow-auto">
              <table className="data" data-testid="psi-table">
                <thead><tr><th>Input</th>{batches.map((b) => <th key={b.id}>{b.as_of_date}</th>)}</tr></thead>
                <tbody>
                  {features.map((f) => (
                    <tr key={f}>
                      <td><code>{f}</code></td>
                      {batches.map((b) => { const r = b.results_json.psi[f]; return <td key={b.id} className="tabular"><span className="mr-2">{fmt(r.psi)}</span><Badge value={r.status} /></td>; })}
                    </tr>
                  ))}
                  <tr><td><em>Model scores</em></td>{batches.map((b) => <td key={b.id} className="tabular"><span className="mr-2">{fmt(b.results_json.score_drift?.psi)}</span><Badge value={b.results_json.score_drift?.status ?? "stable"} /></td>)}</tr>
                  <tr><td>Batch verdict</td>{batches.map((b) => <td key={b.id}><Badge value={b.status} /> <span className="faint text-xs">{b.labels_available ? "outcomes known" : "outcomes not yet known"}</span></td>)}</tr>
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
      <Card title={`Alerts · ${open.length} open, ${mon.alerts.length - open.length} resolved`} subtitle="Every alert has an owner and a due date. Resolving one requires a written reason, which is kept in the audit log.">
        {mon.alerts.length === 0 ? <p className="muted text-sm">No alerts.</p> : (
          <table className="data">
            <thead><tr><th>Severity</th><th>Alert</th><th>Status</th><th>Action</th></tr></thead>
            <tbody>{[...mon.alerts].sort((a, b) => (a.status === "resolved" ? 1 : 0) - (b.status === "resolved" ? 1 : 0)).map((a) => <AlertRow key={a.id} a={a} versionId={mon.model_version} />)}</tbody>
          </table>
        )}
      </Card>
      <Glossary keys={["batch", "psi", "scoreDrift", "auc"]} />
    </div>
  );
}
