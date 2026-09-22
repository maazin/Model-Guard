import { useParams } from "react-router-dom";
import { useVersion } from "../lib/hooks";
import { Badge, Card, ErrorBox, Glossary, Loading, PageHeader, Term, fmt } from "../components/ui";
import { DocumentViewer } from "../components/DocumentViewer";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine, Legend, ScatterChart, Scatter } from "recharts";

const tip = { contentStyle: { background: "var(--surface)", borderColor: "var(--hairline)", borderRadius: 10, fontSize: 12 } };
const axis = { fontSize: 11, fill: "var(--text-3)" };

export function Validation() {
  const { id } = useParams();
  const q = useVersion(id);
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox error={q.error} />;
  const v = q.data!;
  const a = v.artifacts;
  if (!a.roc) {
    return (
      <div className="space-y-6">
        <PageHeader title="Model quality" badges={<Badge value={v.state} />} />
        <Card title="Not yet validated"><p className="muted text-sm">A data scientist runs the validation suite from the Approval page. Results appear here once it has run.</p></Card>
      </div>
    );
  }
  const roc = a.roc.fpr.map((f: number, i: number) => ({ fpr: f, tpr: a.roc.tpr[i] }));
  const cal = a.calibration.mean_predicted.map((p: number | null, i: number) => ({ predicted: p, observed: a.calibration.observed_rate[i], n: a.calibration.bin_count[i] })).filter((d: any) => d.predicted !== null);
  const comp = a.comparator as Record<string, Record<string, any>>;
  const mine = comp[v.model_type];
  const otherType = v.model_type === "champion" ? "baseline" : "champion";
  const other = comp[otherType];
  const conf = a.confusion;
  const fair = a.fairness;
  const ht = a.hypothesis_test?.[0];
  const cfg = v.training_run.config_json ?? {};
  const temporal = cfg.split?.strategy === "temporal";
  const fairnessField = cfg.feature_spec?.fairness_field ?? "fairness_group";
  const better = mine.auc.value > other.auc.value;
  const overlap = mine.auc.lower_ci <= other.auc.upper_ci && other.auc.lower_ci <= mine.auc.upper_ci;
  const rows: [string, string, any][] = [
    ["Ranking accuracy", "auc", "auc"],
    ["Separation", "ks", "ks"],
    ["Forecast error", "brier", "brier"],
    ["Calibration error", "ece", "ece"],
  ];
  return (
    <div className="space-y-8">
      <PageHeader
        title="Model quality"
        lede={
          <>
            All results below come from {mine.n_holdout.value.toLocaleString()} borrowers the model never saw during training
            {temporal ? ", drawn from the most recent period" : " (a random, stratified sample, because this dataset has no dates)"}. The candidate is compared with a simpler
            reference model built the same way.
          </>
        }
        badges={<Badge value={v.state} />}
      />
      <Card
        title="Candidate versus reference model"
        subtitle={
          better
            ? overlap
              ? "The candidate scores higher, but the two ranges overlap, so the difference is not conclusive. Promotion was a human decision."
              : "The candidate scores higher and the ranges do not overlap, so the improvement is unlikely to be chance."
            : "The candidate does not beat the reference model on ranking accuracy; it was kept for other reasons recorded in the model card."
        }
      >
        <table className="data">
          <thead>
            <tr><th>Measure</th><th>{v.model_type === "champion" ? "Candidate (gradient-boosted)" : "Candidate (logistic)"}</th><th>{otherType === "baseline" ? "Reference (logistic)" : "Gradient-boosted"}</th><th className="hidden sm:table-cell">Better is</th></tr>
          </thead>
          <tbody>
            {rows.map(([label, key, m]) => (
              <tr key={key}>
                <td><Term k={key as any}>{label}</Term></td>
                <td className="tabular">{fmt(mine[m].value, 3)} {mine[m].lower_ci !== undefined && <span className="faint">({fmt(mine[m].lower_ci, 2)}–{fmt(mine[m].upper_ci, 2)})</span>}</td>
                <td className="tabular">{fmt(other[m].value, 3)} {other[m].lower_ci !== undefined && <span className="faint">({fmt(other[m].lower_ci, 2)}–{fmt(other[m].upper_ci, 2)})</span>}</td>
                <td className="muted hidden sm:table-cell">{m === "auc" || m === "ks" ? "higher" : "lower"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="faint mt-3 text-[13px]">Ranges in brackets are <Term k="ci">95% confidence intervals</Term>. Nothing is promoted automatically on the strength of this table.</p>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Trade-off between catching defaulters and flagging good borrowers" subtitle="The further the curve sits above the diagonal, the better the model ranks risk.">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={roc} margin={{ left: 0, right: 12, top: 8 }}>
              <CartesianGrid stroke="var(--hairline)" />
              <XAxis dataKey="fpr" type="number" domain={[0, 1]} tick={axis} stroke="var(--hairline)" label={{ value: "Good borrowers flagged", position: "insideBottom", offset: -2, fontSize: 11, fill: "var(--text-3)" }} />
              <YAxis dataKey="tpr" type="number" domain={[0, 1]} tick={axis} stroke="var(--hairline)" label={{ value: "Defaulters caught", angle: -90, position: "insideLeft", fontSize: 11, fill: "var(--text-3)" }} />
              <Tooltip {...tip} formatter={(x: number) => x.toFixed(3)} />
              <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke="var(--text-3)" strokeDasharray="4 4" />
              <Line type="monotone" dataKey="tpr" stroke="var(--series-1)" strokeWidth={2} dot={false} name="model" isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Do the probabilities mean what they say?" subtitle={<>Points on the dotted line are perfectly honest. <Term k="ece">Calibration error</Term>: {fmt(a.calibration.ece, 3)}.</>}>
          <ResponsiveContainer width="100%" height={260}>
            <ScatterChart margin={{ left: 0, right: 12, top: 8 }}>
              <CartesianGrid stroke="var(--hairline)" />
              <XAxis dataKey="predicted" type="number" domain={[0, 1]} tick={axis} stroke="var(--hairline)" name="Predicted" label={{ value: "Predicted default rate", position: "insideBottom", offset: -2, fontSize: 11, fill: "var(--text-3)" }} />
              <YAxis dataKey="observed" type="number" domain={[0, 1]} tick={axis} stroke="var(--hairline)" name="Observed" label={{ value: "Actual default rate", angle: -90, position: "insideLeft", fontSize: 11, fill: "var(--text-3)" }} />
              <Tooltip {...tip} formatter={(x: number) => x.toFixed(3)} />
              <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke="var(--text-3)" strokeDasharray="4 4" />
              <Scatter data={cal} fill="var(--series-1)" line={{ stroke: "var(--series-1)", strokeWidth: 2 }} name="risk bands" isAnimationActive={false} />
            </ScatterChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title={<>What happens at an <Term k="threshold">illustrative cut-off</Term> of {fmt(conf.threshold, 2)}</>} subtitle="Chosen only to show the trade-off. It is not a lending policy.">
          <table className="data w-auto">
            <thead><tr><th></th><th>Flagged</th><th>Not flagged</th></tr></thead>
            <tbody>
              <tr><th>Did default</th><td>{conf.tp.toLocaleString()} caught</td><td>{conf.fn.toLocaleString()} missed</td></tr>
              <tr><th>Did not default</th><td>{conf.fp.toLocaleString()} flagged in error</td><td>{conf.tn.toLocaleString()} correctly cleared</td></tr>
            </tbody>
          </table>
          <p className="muted mt-3 text-sm">
            Of borrowers flagged, {Math.round(conf.precision * 100)}% defaulted (<Term k="precision">precision</Term>); of borrowers who defaulted, {Math.round(conf.recall * 100)}% were flagged (recall). {Math.round(conf.selection_rate * 100)}% of all borrowers would be flagged.
          </p>
        </Card>
        <Card title="How the cut-off changes the picture" subtitle="Moving the cut-off right flags fewer borrowers but misses more defaulters.">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={a.threshold_analysis} margin={{ left: 0, right: 12, top: 8 }}>
              <CartesianGrid stroke="var(--hairline)" />
              <XAxis dataKey="threshold" tick={axis} stroke="var(--hairline)" />
              <YAxis domain={[0, 1]} tick={axis} stroke="var(--hairline)" />
              <Tooltip {...tip} formatter={(x: number) => x.toFixed(3)} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line dataKey="precision" stroke="var(--series-1)" strokeWidth={2} dot={false} isAnimationActive={false} name="flagged who defaulted" />
              <Line dataKey="recall" stroke="var(--series-2)" strokeWidth={2} dot={false} isAnimationActive={false} name="defaulters caught" />
              <Line dataKey="selection_rate" stroke="var(--series-3)" strokeWidth={2} dot={false} isAnimationActive={false} name="share flagged" />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Does it treat groups of borrowers alike?" subtitle={<><Term k="fairness">Fairness diagnostics</Term> by <code>{fairnessField}</code>, which is never used as a model input.</>}>
          {fair ? (
            <>
              <div className="mb-3 grid grid-cols-3 gap-2 text-sm">
                <div><div className="faint text-xs">Flag-rate ratio</div><div className="tabular text-lg font-medium">{fmt(fair.selection_rate_ratio, 2)}</div></div>
                <div><div className="faint text-xs">Defaulters caught, gap</div><div className="tabular text-lg font-medium">{fmt(fair.tpr_difference, 3)}</div></div>
                <div><div className="faint text-xs">Flagged in error, gap</div><div className="tabular text-lg font-medium">{fmt(fair.fpr_difference, 3)}</div></div>
              </div>
              <table className="data">
                <thead><tr><th>Group</th><th>Borrowers</th><th>Flagged</th><th>Defaulters caught</th><th>Flagged in error</th><th>Actual default rate</th><th>Predicted</th></tr></thead>
                <tbody>
                  {Object.entries(fair.groups).map(([g, m]: any) => (
                    <tr key={g}><td>{g}</td><td>{m.n.toLocaleString()}</td><td>{Math.round(m.selection_rate * 100)}%</td><td>{Math.round(m.tpr * 100)}%</td><td>{Math.round(m.fpr * 100)}%</td><td>{Math.round(m.observed_default_rate * 100)}%</td><td>{Math.round(m.mean_predicted * 100)}%</td></tr>
                  ))}
                </tbody>
              </table>
              <p className="faint mt-3 text-[13px]">A flag-rate ratio below 0.80 is a common prompt to look closer. These figures inform a discussion; they are not a legal finding.</p>
            </>
          ) : (
            <p className="muted text-sm">No grouping field is available for this dataset; the reason is recorded in the risk assessment.</p>
          )}
        </Card>
        <Card title="Is the test data like the training data?" subtitle={<Term k="hypothesis">A formal check of one input, so the comparison is fair.</Term>}>
          {ht && (
            <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
              <dt className="muted">Input checked</dt><dd><code>{ht.feature}</code></dd>
              <dt className="muted">Question</dt><dd>Do training and test borrowers share the same distribution of this input?</dd>
              <dt className="muted">Result</dt><dd>{ht.reject_null ? "They differ by more than chance would explain" : "No difference beyond chance"} (p = {ht.p_value < 0.001 ? "< 0.001" : ht.p_value.toFixed(3)}; effect size {fmt(ht.effect_size.cohens_d, 2)}, which is {Math.abs(ht.effect_size.cohens_d) < 0.2 ? "negligible" : Math.abs(ht.effect_size.cohens_d) < 0.5 ? "small" : "material"}).</dd>
              <dt className="muted">Caveat</dt><dd className="muted">{ht.limitation}</dd>
            </dl>
          )}
        </Card>
      </div>
      <Card title="Validation report" subtitle="The written record of every test above, with limitations and reviewer status.">
        <DocumentViewer versionId={v.semantic_version} type="validation_report" />
      </Card>
      <Glossary keys={["auc", "ks", "brier", "ece", "ci", "holdout", "champion", "threshold", "precision", "fairness", "hypothesis"]} />
    </div>
  );
}
