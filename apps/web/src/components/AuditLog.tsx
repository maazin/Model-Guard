import type { AuditEvent } from "../lib/types";
import { fmtDate } from "./ui";

export function AuditLog({ events }: { events: AuditEvent[] }) {
  return (
    <div className="max-h-[50vh] overflow-auto">
      <table className="data">
        <thead>
          <tr>
            <th>When</th>
            <th>Actor</th>
            <th>Action</th>
            <th>Change</th>
            <th>Hash</th>
          </tr>
        </thead>
        <tbody>
          {[...events].reverse().map((e) => (
            <tr key={e.id}>
              <td className="whitespace-nowrap">{fmtDate(e.occurred_at)}</td>
              <td>{e.actor_id}</td>
              <td><code>{e.action}</code></td>
              <td className="muted">
                {e.before_json?.state && <span>{e.before_json.state} → </span>}
                {e.after_json?.state ?? (e.after_json ? JSON.stringify(e.after_json).slice(0, 90) : "")}
              </td>
              <td><code className="faint" title={`prev ${e.previous_hash}`}>{e.event_hash.slice(0, 10)}</code></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
