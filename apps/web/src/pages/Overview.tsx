import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { get } from "../lib/api";
import type { ExecutiveSummary } from "../lib/types";
import { Badge, Card, ErrorBox, Glossary, Loading, PageHeader, Term, fmt } from "../components/ui";

export function Overview() {
  const q = useQuery({ queryKey: ["portfolio"], queryFn: () => get<{ versions: ExecutiveSummary[] }>("/api/v1/portfolio") });
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox error={q.error} />;
  const versions = q.data!.versions;
  const live = versions.filter((v) => v.state === "MONITORING" || v.state === "APPROVED");
  return (
    <div className="space-y-8">
      <PageHeader
        title="Credit-risk models"
        lede={
          <>
            Lenders use models like these to estimate how likely a borrower is to miss payments. ModelGuard makes sure such a model is not used until its evidence is complete and a
            person has signed off, and keeps watching it afterwards. Each card below is one version of a model. {live.length} version{live.length === 1 ? " is" : "s are"} currently
            approved and monitored. New here? <Link className="underline" to="/about">Read why this exists</Link>.
          </>
        }
      />
      <div className="grid gap-4 md:grid-cols-2">
        {versions.map((v) => (
          <Card
            key={v.model_version_id}
            title={
              <Link to={`/versions/${v.model_version}/executive`} className="hover:underline">
                {v.model_version}
              </Link>
            }
            subtitle={v.model_type === "champion" ? "Gradient-boosted candidate" : "Logistic-regression candidate"}
            actions={
              <div className="flex gap-2">
                <Badge value={v.state} />
                <Badge value={v.health} />
              </div>
            }
          >
            <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-sm">
              <dt className="muted">
                <Term k="auc">Ranking accuracy</Term>
              </dt>
              <dd className="tabular">
                {fmt(v.holdout.auc?.value)}{" "}
                {v.holdout.auc?.lower_ci !== undefined && <span className="faint">(likely between {fmt(v.holdout.auc.lower_ci, 2)} and {fmt(v.holdout.auc.upper_ci, 2)})</span>}
              </dd>
              <dt className="muted">
                <Term k="readiness">Evidence</Term>
              </dt>
              <dd>{v.readiness.passed} of {v.readiness.total} requirements met</dd>
              <dt className="muted">Open alerts</dt>
              <dd>
                {v.alerts.open === 0 ? "None" : v.alerts.open}
                {v.alerts.high > 0 && <span style={{ color: "var(--critical)" }}> · {v.alerts.high} high severity</span>}
              </dd>
              <dt className="muted">Batches checked</dt>
              <dd>{v.batches_evaluated}</dd>
            </dl>
            <div className="mt-4 border-t pt-3 text-sm hairline">
              <div className="faint text-xs">What happens next</div>
              <div className="mt-0.5">{v.next_action}</div>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <Link className="btn btn-primary" to={`/versions/${v.model_version}/executive`}>Read the summary</Link>
              <Link className="btn" to={`/versions/${v.model_version}/governance`}>Approval &amp; evidence</Link>
              <Link className="btn" to={`/versions/${v.model_version}/monitoring`}>Monitoring</Link>
            </div>
          </Card>
        ))}
      </div>
      <Glossary keys={["auc", "readiness", "lifecycle", "champion", "batch"]} />
    </div>
  );
}
