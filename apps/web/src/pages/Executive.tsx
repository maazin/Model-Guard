import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { get } from "../lib/api";
import type { ExecutiveSummary } from "../lib/types";
import { Badge, Card, ErrorBox, Glossary, Loading, PageHeader, Stat, fmt } from "../components/ui";

function readAuc(x?: number | null) {
  if (x === null || x === undefined) return "Not yet measured.";
  return `Picks the riskier of two borrowers correctly about ${Math.round(x * 100)} times in 100.`;
}

export function Executive() {
  const { id } = useParams();
  const q = useQuery({ queryKey: ["executive", id], queryFn: () => get<ExecutiveSummary>(`/api/v1/executive-summary/${id}`) });
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox error={q.error} />;
  const s = q.data!;
  return (
    <div className="space-y-8" data-testid="executive">
      <PageHeader title={s.model_version} lede={s.purpose} badges={<><Badge value={s.state} /><Badge value={s.health} /></>} />
      <Card title="Recommendation">
        <p className="text-[19px] font-medium leading-snug">{s.recommendation}</p>
        <p className="muted mt-2 text-sm">Next step: {s.next_action}</p>
      </Card>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Ranking accuracy" term="auc" value={fmt(s.holdout.auc?.value, 2)} reading={<>{readAuc(s.holdout.auc?.value)} The simpler reference model scores {fmt(s.comparator.auc?.value, 2)}.</>} />
        <Stat label="Latest batch" term="batch" value={s.latest_batch ? fmt(s.latest_batch.auc, 2) : "—"} reading={s.latest_batch ? `Accuracy on borrowers scored ${s.latest_batch.as_of_date}; batch status: ${s.latest_batch.status}.` : "No batches checked yet."} />
        <Stat label="Open alerts" value={s.alerts.open} reading={`${s.alerts.high} high severity · ${s.alerts.resolved} already resolved with a written reason.`} />
        <Stat label="Evidence complete" term="readiness" value={`${s.readiness.passed}/${s.readiness.total}`} reading={s.readiness.failing.length ? `Still missing: ${s.readiness.failing.map((f) => f.replace(/_/g, " ")).join(", ")}.` : "Every requirement has evidence on file."} />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Top risks right now">
          {s.top_risks.length === 0 ? <p className="muted text-sm">No open risks.</p> : (
            <ul className="space-y-2 text-sm">
              {s.top_risks.map((r) => (
                <li key={r} className="flex gap-2">
                  <span aria-hidden className="mt-2 inline-block h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: "var(--serious)" }} />
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>
        <Card title="What this model must not be used for">
          <ul className="space-y-2 text-sm">
            {s.limits.map((l) => (
              <li key={l} className="flex gap-2">
                <span aria-hidden className="mt-2 inline-block h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: "var(--neutral)" }} />
                <span>{l}</span>
              </li>
            ))}
          </ul>
        </Card>
      </div>
      <p className="muted text-sm">
        Want the detail behind these numbers? See <Link className="underline" to={`/versions/${s.model_version}/validation`}>model quality</Link>,{" "}
        <Link className="underline" to={`/versions/${s.model_version}/monitoring`}>monitoring</Link> or the <Link className="underline" to={`/versions/${s.model_version}/governance`}>approval record</Link>.
      </p>
      <Glossary keys={["auc", "batch", "readiness", "lifecycle"]} />
    </div>
  );
}
