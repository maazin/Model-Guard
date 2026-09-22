import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { get } from "../lib/api";
import type { ExecutiveSummary } from "../lib/types";
import { Badge, Card, ErrorBox, Loading, Stat, fmt } from "../components/ui";

export function Executive() {
  const { id } = useParams();
  const q = useQuery({ queryKey: ["executive", id], queryFn: () => get<ExecutiveSummary>(`/api/v1/executive-summary/${id}`) });
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox error={q.error} />;
  const s = q.data!;
  return (
    <div className="space-y-6" data-testid="executive">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-semibold">Executive summary · {s.model_version}</h1>
        <Badge value={s.state} />
        <Badge value={s.health} label={`health: ${s.health.replace("_", " ")}`} />
      </div>
      <Card title="Recommendation">
        <p className="text-lg font-medium">{s.recommendation}</p>
        <p className="muted mt-1 text-sm">Next action: {s.next_action}</p>
      </Card>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Holdout AUC" value={fmt(s.holdout.auc?.value)} sub={s.holdout.auc ? `95% CI ${fmt(s.holdout.auc.lower_ci, 2)}–${fmt(s.holdout.auc.upper_ci, 2)} · comparator ${fmt(s.comparator.auc?.value)}` : "not validated"} />
        <Stat label="Latest batch AUC" value={fmt(s.latest_batch?.auc ?? null)} sub={s.latest_batch ? `${s.latest_batch.as_of_date} · status ${s.latest_batch.status}` : "no monitoring yet"} />
        <Stat label="Open alerts" value={s.alerts.open} sub={`${s.alerts.high} high · ${s.alerts.resolved} resolved`} />
        <Stat label="Readiness" value={`${s.readiness.passed}/${s.readiness.total}`} sub={s.readiness.failing.length ? `failing: ${s.readiness.failing.join(", ")}` : "all checks pass"} />
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <Card title="Model purpose"><p className="text-sm">{s.purpose}</p></Card>
        <Card title="Top risks">{s.top_risks.length === 0 ? <p className="muted text-sm">None open.</p> : <ul className="list-disc pl-5 text-sm">{s.top_risks.map((r) => <li key={r}>{r}</li>)}</ul>}</Card>
        <Card title="Limits"><ul className="list-disc pl-5 text-sm">{s.limits.map((l) => <li key={l}>{l}</li>)}</ul></Card>
      </div>
    </div>
  );
}
