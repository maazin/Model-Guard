import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { get } from "../lib/api";
import { Badge, Card, ErrorBox, Glossary, Loading, PageHeader, Term, fmt } from "../components/ui";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine, ReferenceDot, Legend } from "recharts";

interface SimData { model_version: string; state: string; illustrative_threshold: number | null; group_field: string | null; auc: number | null; n: number; score: number[]; outcome: number[]; group: string[]; source_id: string }

const tip = { contentStyle: { background: "var(--surface)", borderColor: "var(--hairline)", borderRadius: 10, fontSize: 12 } };
const axis = { fontSize: 11, fill: "var(--text-3)" };
const money = (x: number) => (x < 0 ? "−" : "") + Math.abs(Math.round(x)).toLocaleString();

function evaluate(d: SimData, cutoff: number, margin: number, loss: number) {
  let tp = 0, fp = 0, tn = 0, fn = 0;
  const byGroup: Record<string, { n: number; declined: number }> = {};
  for (let i = 0; i < d.n; i++) {
    const declined = d.score[i] >= cutoff;
    const bad = d.outcome[i] === 1;
    if (declined && bad) tp++; else if (declined && !bad) fp++; else if (!declined && bad) fn++; else tn++;
    if (d.group.length) {
      const g = d.group[i];
      byGroup[g] ??= { n: 0, declined: 0 };
      byGroup[g].n++;
      if (declined) byGroup[g].declined++;
    }
  }
  const approved = tn + fn;
  const pnl = tn * margin - fn * loss;
  const rates = Object.values(byGroup).map((g) => g.declined / g.n);
  const ratio = rates.length > 1 && Math.max(...rates) > 0 ? Math.min(...rates) / Math.max(...rates) : null;
  return { tp, fp, tn, fn, approved, declined: tp + fp, pnl, byGroup, ratio, declineRate: (tp + fp) / d.n, defaultRateAmongApproved: approved ? fn / approved : 0 };
}

export function Simulator() {
  const { id } = useParams();
  const q = useQuery({ queryKey: ["simulator", id], queryFn: () => get<SimData>(`/api/v1/model-versions/${id}/simulator`) });
  const [cutoff, setCutoff] = useState<number | null>(null);
  const [margin, setMargin] = useState(500);
  const [loss, setLoss] = useState(1500);
  const d = q.data;
  const effectiveCutoff = cutoff ?? d?.illustrative_threshold ?? 0.3;
  const result = useMemo(() => (d ? evaluate(d, effectiveCutoff, margin, loss) : null), [d, effectiveCutoff, margin, loss]);
  const curve = useMemo(() => {
    if (!d) return [];
    const rows = [];
    for (let c = 0.02; c <= 0.98; c += 0.02) {
      const r = evaluate(d, +c.toFixed(2), margin, loss);
      rows.push({ cutoff: +c.toFixed(2), pnl: r.pnl, approved: r.approved / d.n, caught: r.tp + r.fn ? r.tp / (r.tp + r.fn) : 0 });
    }
    return rows;
  }, [d, margin, loss]);
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox error={q.error} />;
  if (!d || !result) return null;
  const everyone = evaluate(d, 1.01, margin, loss);
  const best = curve.reduce((a, b) => (b.pnl > a.pnl ? b : a), curve[0]);
  const baseRate = d.outcome.reduce((a, b) => a + b, 0) / d.n;
  return (
    <div className="space-y-8" data-testid="simulator">
      <PageHeader
        title="Try the cut-off"
        lede={
          <>
            The model gives each of these {d.n.toLocaleString()} held-out borrowers a risk score between 0 and 1; {Math.round(baseRate * 100)}% of them actually defaulted. A lender must
            choose a score above which to decline. Move the cut-off and change the money assumptions to see the trade-off the model creates. Nothing here is a real lending policy.
          </>
        }
        badges={<Badge value={d.state} />}
      />

      <div className="grid gap-4 lg:grid-cols-[340px_1fr]">
        <Card title="Your choices">
          <div className="space-y-5 text-sm">
            <label className="block">
              <div className="flex items-baseline justify-between">
                <span className="font-medium">Decline borrowers scoring above</span>
                <span className="tabular text-lg font-semibold">{effectiveCutoff.toFixed(2)}</span>
              </div>
              <input type="range" min={0.02} max={0.98} step={0.01} value={effectiveCutoff} onChange={(e) => setCutoff(+e.target.value)} className="mt-2 w-full" aria-label="Cut-off" data-testid="cutoff" />
              <div className="faint mt-1 flex justify-between text-xs"><span>decline almost no one</span><span>decline almost everyone</span></div>
              {d.illustrative_threshold !== null && (
                <button className="btn btn-quiet mt-1 text-xs" onClick={() => setCutoff(null)}>Reset to the illustrative cut-off ({d.illustrative_threshold.toFixed(2)})</button>
              )}
            </label>
            <div className="border-t pt-4 hairline">
              <div className="faint mb-2 text-xs uppercase tracking-wide">Money assumptions (per loan, any currency)</div>
              <label className="mb-3 block">
                <span className="muted">Profit from a loan that is repaid</span>
                <input type="number" className="field mt-1" value={margin} min={0} step={50} onChange={(e) => setMargin(+e.target.value || 0)} aria-label="Profit per repaid loan" />
              </label>
              <label className="block">
                <span className="muted">Loss from a loan that defaults</span>
                <input type="number" className="field mt-1" value={loss} min={0} step={100} onChange={(e) => setLoss(+e.target.value || 0)} aria-label="Loss per defaulted loan" />
              </label>
              <p className="faint mt-2 text-xs">Illustrative round numbers. Change them and watch the best cut-off move: the more a default costs relative to the profit on a good loan, the stricter the lender should be.</p>
            </div>
          </div>
        </Card>

        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="card">
              <div className="muted text-sm">You would approve</div>
              <div className="tabular mt-1 text-[28px] font-semibold leading-none">{Math.round((result.approved / d.n) * 100)}%</div>
              <div className="faint mt-2 text-[13px]">{result.approved.toLocaleString()} of {d.n.toLocaleString()} applicants. {Math.round(result.defaultRateAmongApproved * 100)}% of them would go on to default (versus {Math.round(baseRate * 100)}% if you approved everyone).</div>
            </div>
            <div className="card">
              <div className="muted text-sm">Defaulters avoided</div>
              <div className="tabular mt-1 text-[28px] font-semibold leading-none">{result.tp.toLocaleString()}</div>
              <div className="faint mt-2 text-[13px]">{Math.round((result.tp / (result.tp + result.fn)) * 100)}% of all defaulters declined; {result.fn.toLocaleString()} still slip through.</div>
            </div>
            <div className="card">
              <div className="muted text-sm">Good customers turned away</div>
              <div className="tabular mt-1 text-[28px] font-semibold leading-none">{result.fp.toLocaleString()}</div>
              <div className="faint mt-2 text-[13px]">{Math.round((result.fp / (result.fp + result.tn)) * 100)}% of borrowers who would have repaid are declined at this cut-off.</div>
            </div>
          </div>
          <Card title="What it adds up to" subtitle="Profit on repaid loans minus losses on defaults, for the approved borrowers only.">
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-xl p-3" style={{ background: "var(--surface-2)" }}>
                <div className="faint text-xs">Your cut-off ({effectiveCutoff.toFixed(2)})</div>
                <div className="tabular text-xl font-semibold" style={{ color: result.pnl >= 0 ? "var(--good)" : "var(--critical)" }} data-testid="pnl">{money(result.pnl)}</div>
              </div>
              <div className="rounded-xl p-3" style={{ background: "var(--surface-2)" }}>
                <div className="faint text-xs">Approve everyone (no model)</div>
                <div className="tabular text-xl font-semibold" style={{ color: everyone.pnl >= 0 ? "var(--good)" : "var(--critical)" }}>{money(everyone.pnl)}</div>
              </div>
              <div className="rounded-xl p-3" style={{ background: "var(--surface-2)" }}>
                <div className="faint text-xs">Best cut-off under these assumptions ({best.cutoff.toFixed(2)})</div>
                <div className="tabular text-xl font-semibold" style={{ color: "var(--good)" }}>{money(best.pnl)}</div>
              </div>
            </div>
            <p className="muted mt-3 text-sm">
              {result.pnl > everyone.pnl
                ? `Using the model at this cut-off is worth ${money(result.pnl - everyone.pnl)} more than lending to everyone.`
                : `At this cut-off the model is worth ${money(everyone.pnl - result.pnl)} less than lending to everyone — you are turning away too many good customers for the defaults you avoid.`}{" "}
              {Math.abs(best.cutoff - effectiveCutoff) > 0.015 && <>Moving the cut-off to {best.cutoff.toFixed(2)} would add {money(best.pnl - result.pnl)}.</>}
            </p>
          </Card>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Profit at every possible cut-off" subtitle="The curve is what the money assumptions do to the model's ranking. The dot is your current choice.">
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={curve} margin={{ left: 8, right: 16, top: 8 }}>
              <CartesianGrid stroke="var(--hairline)" />
              <XAxis dataKey="cutoff" tick={axis} stroke="var(--hairline)" />
              <YAxis tick={axis} stroke="var(--hairline)" tickFormatter={(v) => (Math.abs(v) >= 1000 ? `${Math.round(v / 1000)}k` : String(v))} />
              <Tooltip {...tip} formatter={(v: number) => money(v)} labelFormatter={(l) => `cut-off ${l}`} />
              <ReferenceLine y={everyone.pnl} stroke="var(--series-2)" strokeDasharray="4 4" label={{ value: "approve everyone", fontSize: 10, fill: "var(--text-3)", position: "insideTopRight" }} />
              <Line dataKey="pnl" stroke="var(--series-1)" strokeWidth={2} dot={false} isAnimationActive={false} name="profit" />
              <ReferenceDot x={+effectiveCutoff.toFixed(2)} y={result.pnl} r={6} fill="var(--series-1)" stroke="var(--surface)" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Approvals and defaulters caught at every cut-off" subtitle="Lowering the cut-off catches more defaulters but approves fewer people.">
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={curve} margin={{ left: 8, right: 16, top: 8 }}>
              <CartesianGrid stroke="var(--hairline)" />
              <XAxis dataKey="cutoff" tick={axis} stroke="var(--hairline)" />
              <YAxis domain={[0, 1]} tick={axis} stroke="var(--hairline)" tickFormatter={(v) => `${Math.round(v * 100)}%`} />
              <Tooltip {...tip} formatter={(v: number) => `${Math.round(v * 100)}%`} labelFormatter={(l) => `cut-off ${l}`} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <ReferenceLine x={+effectiveCutoff.toFixed(2)} stroke="var(--text-3)" strokeDasharray="4 4" />
              <Line dataKey="approved" stroke="var(--series-1)" strokeWidth={2} dot={false} isAnimationActive={false} name="share approved" />
              <Line dataKey="caught" stroke="var(--series-2)" strokeWidth={2} dot={false} isAnimationActive={false} name="defaulters declined" />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {d.group_field && result.ratio !== null && (
        <Card title={<>Does your cut-off treat groups alike? <span className="faint font-normal">· selection-rate ratio by <code>{d.group_field}</code></span></>} subtitle="Share of each group declined at your cut-off. The grouping field is never a model input; this is a diagnostic, not a legal test.">
          <div className="grid gap-3 sm:grid-cols-[auto_1fr] sm:items-center">
            <div>
              <div className="faint text-xs">Decline-rate ratio (lowest ÷ highest)</div>
              <div className="tabular text-2xl font-semibold" style={{ color: result.ratio < 0.8 ? "var(--warning)" : "var(--good)" }}>{fmt(result.ratio, 2)}</div>
              <div className="faint text-xs">{result.ratio < 0.8 ? "Below the 0.80 rule of thumb: worth a closer look." : "Above the 0.80 rule of thumb."}</div>
            </div>
            <table className="data">
              <thead><tr><th>Group</th><th>Borrowers</th><th>Declined</th></tr></thead>
              <tbody>{Object.entries(result.byGroup).map(([g, v]) => <tr key={g}><td>{g}</td><td>{v.n.toLocaleString()}</td><td>{Math.round((v.declined / v.n) * 100)}%</td></tr>)}</tbody>
            </table>
          </div>
        </Card>
      )}

      <Card title="What this shows">
        <ul className="list-disc space-y-1.5 pl-5 text-sm">
          <li>The model does not decide anything; it ranks. The cut-off is a business choice, and the right one depends entirely on what a default costs relative to what a good loan earns.</li>
          <li>A better <Term k="auc">ranking accuracy</Term> makes the profit curve higher everywhere; it does not tell you where to cut.</li>
          <li>The two error types trade against each other: every defaulter you avoid costs you some good customers. That is the <Term k="precision" hideAbbr>precision / recall</Term> trade-off in money.</li>
          <li>Moving the cut-off can change how each group of borrowers is treated even though the model never sees the group — which is why fairness is checked at the chosen cut-off, not just once.</li>
        </ul>
        <p className="muted mt-3 text-sm">Scores come from <Link className="underline" to={`/versions/${d.model_version}/validation`}>the model quality tests</Link> for {d.model_version}; borrowers are held-out records with known outcomes.</p>
      </Card>
      <Glossary keys={["threshold", "precision", "auc", "ece", "fairness", "holdout"]} />
    </div>
  );
}
