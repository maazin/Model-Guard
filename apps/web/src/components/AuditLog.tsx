import type { AuditEvent } from "../lib/types";
import { fmtDate } from "./ui";
import { STATE_LABEL } from "../lib/glossary";

const ACTION_LABEL: Record<string, string> = {
  "model_version.registered": "Version registered",
  "model_version.validated": "Validation completed",
  "model_version.submit_review": "Submitted for review",
  "model_version.submit_review_blocked": "Submission blocked by readiness checks",
  "model_version.approve": "Approved",
  "model_version.reject": "Rejected",
  "model_version.start_monitoring": "Monitoring started",
  "model_version.retire": "Retired",
  "model_version.reopen": "Reopened as draft",
  "model_version.narrative_updated": "Documentation updated",
  "controls.replaced": "Controls updated",
  "document.written": "Document written",
  "alert.created": "Alert raised",
  "alert.investigating": "Alert under investigation",
  "alert.resolved": "Alert resolved",
  "monitoring_batch.evaluated": "Batch checked",
  "training_run.queued": "Training queued",
  "training_run.completed": "Training completed",
  "snapshot.imported": "Data imported",
  "data_source.registered": "Data source registered",
};

function describe(e: AuditEvent): string {
  const b = e.before_json?.state;
  const a = e.after_json?.state;
  if (b && a) return `${STATE_LABEL[b] ?? b} → ${STATE_LABEL[a] ?? a}${e.after_json?.rationale ? ` — “${e.after_json.rationale}”` : ""}`;
  if (e.after_json?.blocking_checks) return `Missing: ${e.after_json.blocking_checks.join(", ").replace(/_/g, " ")}`;
  if (e.after_json?.keys) return `Sections: ${e.after_json.keys.join(", ").replace(/_/g, " ")}`;
  return "";
}

export function AuditLog({ events }: { events: AuditEvent[] }) {
  return (
    <div className="max-h-[50vh] overflow-auto">
      <table className="data">
        <thead>
          <tr>
            <th>When</th>
            <th>Who</th>
            <th>What</th>
            <th className="hidden md:table-cell">Fingerprint</th>
          </tr>
        </thead>
        <tbody>
          {[...events].reverse().map((e) => (
            <tr key={e.id}>
              <td className="whitespace-nowrap">{fmtDate(e.occurred_at)}</td>
              <td>{e.actor_id.replace(/_/g, " ")}</td>
              <td>
                <div>{ACTION_LABEL[e.action] ?? e.action}</div>
                <div className="muted text-xs">{describe(e)}</div>
              </td>
              <td className="hidden md:table-cell"><code className="faint text-xs" title={`links to ${e.previous_hash.slice(0, 10)}…`}>{e.event_hash.slice(0, 10)}</code></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
