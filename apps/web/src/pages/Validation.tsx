import { useParams } from "react-router-dom";
import { useVersion } from "../lib/hooks";
import { Badge, Card, ErrorBox, Loading, fmt } from "../components/ui";
import { DocumentViewer } from "../components/DocumentViewer";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine, Legend, ScatterChart, Scatter } from "recharts";

const tip = { contentStyle: { background: "var(--surface-1)", borderColor: "var(--border)", fontSize: 12 } };

export function Validation() {
  const { id } = useParams();
  const q = useVersion(id);
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox error={q.error} />;
  const v = q.data!;
  const a = v.artifacts;
  if (!a.roc) {
    return (
      <Card title="Validation">
        <p className="muted text-sm">This version has not been validated yet. A data scientist can run validation from the Governance page.</p>
      </Card>
    );
  }
  const roc = a.roc.fpr.map((f: number, i: number) => ({ fpr: f, tpr: a.roc.tpr[i] }));
  const cal = a.calibration.mean_predicted.map((p: number | null, i: number) => ({ predicted: p, observed: a.calibration.observed_rate[i], n: a.calibration.bin_count[i] })).filter((d: any) => d.predicted !== null);
  const comp = a.comparator as Record<string, Record<string, any>>;
  const mine = comp[v.model_type];
  const other = comp[v.model_type === "champion" ? "baseline" : "champion"];
  const conf = a.confusion;
  const fair = a.fairness;
  const ht = a.hypothesis_test?.[0];
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-semibold">Validation · {v.semantic_version}</h1>
        <Badge value={v.state} />
      </div>
      <Card title="Holdout comparison (temporal test partition)">
        <table className="data">
          <thead>
            <tr><th>Metric</th><th>{v.model_type} (registered)</th><th>{v.model_type === "champion" ? "baseline" : "champion"}</th></tr>
          </thead>
          <tbody>
            {["auc", "ks", "brier", "ece"].map((m) => (
              <tr key={m}>
                <td className="uppercase">{m}</td>
                <td className="tabular-nums">{fmt(mine[m].value, 4)} {mine[m].lower_ci !== undefined && <span className="faint">[{fmt(mine[m].lower_ci)}, {fmt(mine[m].upper_ci)}]</span>}</td>
                <td className="tabular-nums">{fmt(other[m].value, 4)} {other[m].lower_ci !== undefined && <span className="faint">[{fmt(other[m].lower_ci)}, {fmt(other[m].upper_ci)}]</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="faint mt-2 text-xs">95% percentile bootstrap intervals; differences inside the interval are noise. No automatic promotion is derived from this table.</p>
      </Card>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="ROC curve">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={roc} margin={{ left: 0, right: 12, top: 8 }}>
              <CartesianGrid stroke="var(--border)" />
              <XAxis dataKey="fpr" type="number" domain={[0, 1]} tick={{ fontSize: 11 }} stroke="var(--text-muted)" label={{ value: "False positive rate", position: "insideBottom", offset: -2, fontSize: 11 }} />
              <YAxis dataKey="tpr" type="number" domain={[0, 1]} tick={{ fontSize: 11 }} stroke="var(--text-muted)" label={{ value: "True positive rate", angle: -90, position: "insideLeft", fontSize: 11 }} />
              <Tooltip {...tip} formatter={(x: number) => x.toFixed(3)} />
              <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke="var(--text-muted)" strokeDasharray="4 4" />
              <Line type="monotone" dataKey="tpr" stroke="var(--series-1)" strokeWidth={2} dot={false} name="ROC" isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
        <Card title={`Calibration (ECE ${fmt(a.calibration.ece, 4)})`}>
          <ResponsiveContainer width="100%" height={260}>
            <ScatterChart margin={{ left: 0, right: 12, top: 8 }}>
              <CartesianGrid stroke="var(--border)" />
              <XAxis dataKey="predicted" type="number" domain={[0, 1]} tick={{ fontSize: 11 }} stroke="var(--text-muted)" name="Mean predicted" label={{ value: "Mean predicted PD", position: "insideBottom", offset: -2, fontSize: 11 }} />
              <YAxis dataKey="observed" type="number" domain={[0, 1]} tick={{ fontSize: 11 }} stroke="var(--text-muted)" name="Observed" label={{ value: "Observed rate", angle: -90, position: "insideLeft", fontSize: 11 }} />
              <Tooltip {...tip} formatter={(x: number) => x.toFixed(3)} />
              <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke="var(--text-muted)" strokeDasharray="4 4" />
              <Scatter data={cal} fill="var(--series-1)" line={{ stroke: "var(--series-1)", strokeWidth: 2 }} name="Bins" isAnimationActive={false} />
            </ScatterChart>
          </ResponsiveContainer>
        </Card>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title={`Confusion matrix at illustrative threshold ${fmt(conf.threshold, 2)}`}>
          <p className="faint mb-2 text-xs">Threshold chosen to maximise F1 on the validation partition. Illustrative only — not a lending policy.</p>
          <table className="data w-auto">
            <thead><tr><th></th><th>Predicted default</th><th>Predicted non-default</th></tr></thead>
            <tbody>
              <tr><th>Actual default</th><td>TP {conf.tp}</td><td>FN {conf.fn}</td></tr>
              <tr><th>Actual non-default</th><td>FP {conf.fp}</td><td>TN {conf.tn}</td></tr>
            </tbody>
          </table>
          <p className="muted mt-2 text-xs">precision {fmt(conf.precision)} · recall {fmt(conf.recall)} · specificity {fmt(conf.specificity)} · F1 {fmt(conf.f1)} · selection rate {fmt(conf.selection_rate)}</p>
        </Card>
        <Card title="Threshold analysis">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={a.threshold_analysis} margin={{ left: 0, right: 12, top: 8 }}>
              <CartesianGrid stroke="var(--border)" />
              <XAxis dataKey="threshold" tick={{ fontSize: 11 }} stroke="var(--text-muted)" />
              <YAxis domain={[0, 1]} tick={{ fontSize: 11 }} stroke="var(--text-muted)" />
              <Tooltip {...tip} formatter={(x: number) => x.toFixed(3)} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line dataKey="precision" stroke="var(--series-1)" strokeWidth={2} dot={false} isAnimationActive={false} />
              <Line dataKey="recall" stroke="var(--series-2)" strokeWidth={2} dot={false} isAnimationActive={false} />
              <Line dataKey="selection_rate" stroke="var(--series-3)" strokeWidth={2} dot={false} isAnimationActive={false} name="selection rate" />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Fairness diagnostics (synthetic grouping field)">
          {fair ? (
            <>
              <div className="mb-2 flex flex-wrap gap-4 text-sm">
                <span>Selection-rate ratio <strong>{fmt(fair.selection_rate_ratio)}</strong></span>
                <span>TPR difference <strong>{fmt(fair.tpr_difference)}</strong></span>
                <span>FPR difference <strong>{fmt(fair.fpr_difference)}</strong></span>
              </div>
              <table className="data">
                <thead><tr><th>Group</th><th>n</th><th>Selection</th><th>TPR</th><th>FPR</th><th>Observed</th><th>Predicted</th><th>ECE</th></tr></thead>
                <tbody>
                  {Object.entries(fair.groups).map(([g, m]: any) => (
                    <tr key={g}><td>{g}</td><td>{m.n}</td><td>{fmt(m.selection_rate)}</td><td>{fmt(m.tpr)}</td><td>{fmt(m.fpr)}</td><td>{fmt(m.observed_default_rate)}</td><td>{fmt(m.mean_predicted)}</td><td>{fmt(m.ece)}</td></tr>
                  ))}
                </tbody>
              </table>
              <p className="faint mt-2 text-xs">{fair.disclaimer}</p>
            </>
          ) : (
            <p className="muted text-sm">No grouping field available; see the risk assessment for the documented reason.</p>
          )}
        </Card>
        <Card title="Hypothesis test">
          {ht && (
            <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-sm">
              <dt className="muted">Test</dt><dd>{ht.test} on <code>{ht.feature}</code> (train vs. holdout)</dd>
              <dt className="muted">H0</dt><dd>{ht.null_hypothesis}</dd>
              <dt className="muted">Statistic</dt><dd>D = {fmt(ht.statistic, 4)}; p = {ht.p_value.toExponential(2)}; Cohen's d = {fmt(ht.effect_size.cohens_d)}</dd>
              <dt className="muted">Result</dt><dd>{ht.reject_null ? "reject" : "do not reject"} H0 at α = {ht.alpha}</dd>
              <dt className="muted">Assumptions</dt><dd>{ht.assumptions.join(", ")}</dd>
              <dt className="muted">Limitation</dt><dd className="muted">{ht.limitation}</dd>
            </dl>
          )}
        </Card>
      </div>
      <Card title="Validation report">
        <DocumentViewer versionId={v.semantic_version} type="validation_report" />
      </Card>
    </div>
  );
}
