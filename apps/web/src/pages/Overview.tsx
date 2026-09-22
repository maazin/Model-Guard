import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { get } from "../lib/api";
import type { ExecutiveSummary } from "../lib/types";
import { Badge, Card, ErrorBox, Loading, fmt } from "../components/ui";

export function Overview() {
  const q = useQuery({ queryKey: ["portfolio"], queryFn: () => get<{ versions: ExecutiveSummary[] }>("/api/v1/portfolio") });
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox error={q.error} />;
  const versions = q.data!.versions;
  const active = versions.find((v) => v.state === "MONITORING" || v.state === "APPROVED");
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Portfolio overview</h1>
        <p className="muted text-sm">Probability-of-default model lifecycle: {versions.length} registered version(s). Active model: {active ? active.model_version : "none"}.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {versions.map((v) => (
          <Card
            key={v.model_version_id}
            title={
              <Link to={`/versions/${v.model_version}`} className="hover:underline">
                {v.model_version}
              </Link>
            }
            actions={<Badge value={v.state} />}
          >
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <Badge value={v.health} label={`health: ${v.health.replace("_", " ")}`} />
              <span className="muted">{v.model_type}</span>
            </div>
            <dl className="mt-3 grid grid-cols-2 gap-x-3 gap-y-1 text-sm">
              <dt className="muted">Holdout AUC</dt>
              <dd className="tabular-nums">{fmt(v.holdout.auc?.value)} {v.holdout.auc?.lower_ci !== undefined && <span className="faint text-xs">[{fmt(v.holdout.auc.lower_ci, 2)}–{fmt(v.holdout.auc.upper_ci, 2)}]</span>}</dd>
              <dt className="muted">Readiness</dt>
              <dd>{v.readiness.passed}/{v.readiness.total} checks</dd>
              <dt className="muted">Open alerts</dt>
              <dd>{v.alerts.open} {v.alerts.high > 0 && <span style={{ color: "var(--status-critical)" }}>({v.alerts.high} high)</span>}</dd>
              <dt className="muted">Batches</dt>
              <dd>{v.batches_evaluated}</dd>
            </dl>
            <div className="mt-3 border-t pt-2 text-xs" style={{ borderColor: "var(--border)" }}>
              <div className="faint uppercase tracking-wide">Next required action</div>
              <div className="mt-1">{v.next_action}</div>
            </div>
            {v.top_risks.length > 0 && (
              <ul className="mt-2 list-disc pl-4 text-xs" style={{ color: "var(--text-secondary)" }}>
                {v.top_risks.slice(0, 3).map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
            )}
            <div className="mt-3 flex gap-2 text-xs">
              <Link className="btn" to={`/versions/${v.model_version}/governance`}>Governance</Link>
              <Link className="btn" to={`/versions/${v.model_version}/monitoring`}>Monitoring</Link>
              <Link className="btn" to={`/versions/${v.model_version}/executive`}>Executive</Link>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
