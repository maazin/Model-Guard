import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useParams } from "react-router-dom";
import { useCurrentUser, useVersion } from "../lib/hooks";
import { STATIC_DEMO, post } from "../lib/api";
import { Badge, Card, ErrorBox, Loading, fmtDate } from "../components/ui";
import { DocumentViewer } from "../components/DocumentViewer";

const DOC_TYPES = ["intended_use", "model_card", "data_lineage", "validation_report", "monitoring_plan", "control_matrix", "risk_assessment", "change_log"];

function useAction(id: string) {
  const qc = useQueryClient();
  const [error, setError] = useState<any>(null);
  const m = useMutation({
    mutationFn: ({ path, body }: { path: string; body?: unknown }) => post(`/api/v1/model-versions/${id}${path}`, body),
    onSuccess: () => { setError(null); qc.invalidateQueries(); },
    onError: setError,
  });
  return { m, error, setError };
}

function Copilot({ id }: { id: string }) {
  const [question, setQuestion] = useState(`What evidence is missing before ${id} can move to approved?`);
  const m = useMutation({ mutationFn: () => post(`/api/v1/model-versions/${id}/copilot/query`, { question }) });
  const r = m.data;
  return (
    <div className="space-y-2">
      <p className="faint text-xs">Retrieval is limited to this version's governance documents. The copilot cannot approve anything and never sees loan rows.{STATIC_DEMO && " In this hosted demo the answer is precomputed for the default question."}</p>
      <textarea className="btn w-full" rows={2} value={question} onChange={(e) => setQuestion(e.target.value)} aria-label="Copilot question" data-testid="copilot-question" />
      <button className="btn btn-primary" onClick={() => m.mutate()} disabled={m.isPending || !question.trim()} data-testid="copilot-ask">Ask</button>
      {m.error && <ErrorBox error={m.error} />}
      {r && (
        <div className="space-y-2 text-sm" data-testid="copilot-answer">
          <div className="flex flex-wrap gap-2 text-xs"><Badge value={r.status === "ok" ? "pass" : "fail"} label={`provider ${r.provider}`} /><span className="faint">{r.latency_ms} ms · confidence {r.response.confidence}</span></div>
          <p>{r.response.answer}</p>
          <ul className="space-y-1">
            {r.response.missing_requirements.filter((x: any) => x.status !== "present").map((x: any) => (
              <li key={x.requirement}><Badge value="fail" label={x.status} /> <strong>{x.requirement}</strong>{x.evidence.length > 0 && <ul className="muted list-disc pl-6 text-xs">{x.evidence.map((e: string) => <li key={e}>{e}</li>)}</ul>}</li>
            ))}
          </ul>
          <div className="text-xs"><span className="muted">Citations:</span> {r.response.citations.map((c: any) => <code key={`${c.document_id}-${c.section}`} className="mr-2">{c.document_id} › {c.section}</code>)}</div>
          <p className="faint text-xs">{r.response.disclaimer}</p>
        </div>
      )}
    </div>
  );
}

export function Governance() {
  const { id } = useParams();
  const q = useVersion(id);
  const { m, error } = useAction(id!);
  const role = useCurrentUser();
  const [rationale, setRationale] = useState("");
  const [reason, setReason] = useState("");
  const [doc, setDoc] = useState("model_card");
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox error={q.error} />;
  const v = q.data!;
  const failing = v.readiness.filter((c) => c.status === "fail");
  const isDS = role === "data_scientist";
  const isReviewer = role === "reviewer";
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-semibold">Governance review · {v.semantic_version}</h1>
        <Badge value={v.state} />
        <span className="muted text-sm">acting as <strong>{role}</strong></span>
      </div>
      {error && <ErrorBox error={error} />}
      <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
        <Card title={`Readiness checklist · ${v.readiness.length - failing.length}/${v.readiness.length} passing`}>
          <ul className="space-y-2" data-testid="readiness-list">
            {v.readiness.map((c) => (
              <li key={c.check_name} className="rounded border p-2" style={{ borderColor: "var(--border)" }}>
                <div className="flex items-center gap-2 text-sm"><Badge value={c.status} /><strong>{c.check_name.replace(/_/g, " ")}</strong></div>
                {c.missing.length > 0 && <ul className="mt-1 list-disc pl-6 text-xs" style={{ color: "var(--text-secondary)" }} data-testid="missing-evidence">{c.missing.map((mm) => <li key={mm}>{mm}</li>)}</ul>}
              </li>
            ))}
          </ul>
        </Card>
        <div className="space-y-4">
          <Card title="Actions">
            <div className="space-y-2 text-sm">
              {isDS && (v.state === "DRAFT" || v.state === "VALIDATED") && <button className="btn w-full" onClick={() => m.mutate({ path: "/validate" })} disabled={m.isPending}>Run validation suite</button>}
              {isDS && v.state === "VALIDATED" && <button className="btn btn-primary w-full" onClick={() => m.mutate({ path: "/submit-review" })} disabled={m.isPending} data-testid="submit-review">Submit for review</button>}
              {isDS && v.state === "REJECTED" && <button className="btn w-full" onClick={() => m.mutate({ path: "/reopen" })} disabled={m.isPending}>Reopen as draft</button>}
              {isReviewer && v.state === "PENDING_REVIEW" && (
                <div className="space-y-2" data-testid="decision-form">
                  <label className="muted text-xs" htmlFor="rationale">Reviewer rationale (recorded in the audit log)</label>
                  <textarea id="rationale" className="btn w-full" rows={3} value={rationale} onChange={(e) => setRationale(e.target.value)} />
                  <div className="flex gap-2">
                    <button className="btn btn-primary flex-1" disabled={m.isPending || rationale.length < 3} onClick={() => m.mutate({ path: "/decision", body: { decision: "approve", rationale } })} data-testid="approve">Approve</button>
                    <button className="btn btn-danger flex-1" disabled={m.isPending || rationale.length < 3} onClick={() => m.mutate({ path: "/decision", body: { decision: "reject", rationale } })} data-testid="reject">Reject</button>
                  </div>
                </div>
              )}
              {isReviewer && (v.state === "APPROVED" || v.state === "MONITORING") && (
                <div className="space-y-2">
                  <input className="btn w-full" placeholder="Retirement reason" value={reason} onChange={(e) => setReason(e.target.value)} />
                  <button className="btn w-full" disabled={m.isPending || reason.length < 3} onClick={() => m.mutate({ path: "/retire", body: { reason } })}>Retire version</button>
                </div>
              )}
              {!isDS && !isReviewer && <p className="muted text-xs">Risk leaders have read-only access. Switch role to act.</p>}
              {isDS && v.state === "PENDING_REVIEW" && <p className="muted text-xs">Awaiting reviewer decision. Documents and controls are frozen.</p>}
              {isReviewer && (v.state === "DRAFT" || v.state === "VALIDATED") && <p className="muted text-xs">Nothing to decide until the data scientist submits for review.</p>}
            </div>
          </Card>
          <Card title="Decisions">
            {v.decisions.length === 0 ? <p className="muted text-sm">No reviewer decision yet.</p> : (
              <ul className="space-y-2 text-sm">{v.decisions.map((d) => <li key={d.id}><Badge value={d.decision} /> <span className="muted">{d.reviewer_id} · {fmtDate(d.decided_at)}</span><div className="text-xs">{d.rationale}</div></li>)}</ul>
            )}
          </Card>
        </div>
      </div>
      <Card title={`Control matrix (${v.controls.length} controls)`}>
        {v.controls.length === 0 ? <p className="muted text-sm">No controls recorded. <code>PUT /api/v1/model-versions/{'{id}'}/controls</code> as data_scientist.</p> : (
          <table className="data"><thead><tr><th>Control</th><th>Owner</th><th>Frequency</th><th>Status</th><th>Test evidence</th><th>Evidence</th></tr></thead>
            <tbody>{v.controls.map((c) => <tr key={c.id}><td>{c.control_name}<div className="faint text-xs">{c.description}</div></td><td>{c.owner}</td><td>{c.frequency}</td><td><Badge value={c.status === "planned" ? "fail" : "pass"} label={c.status} /></td><td className="text-xs">{c.test_evidence}</td><td className="text-xs"><code>{c.evidence_uri}</code></td></tr>)}</tbody>
          </table>
        )}
      </Card>
      <Card title="Documents" actions={<select className="btn" value={doc} onChange={(e) => setDoc(e.target.value)} aria-label="Document type">{DOC_TYPES.map((t) => { const d = v.documents.find((x) => x.type === t); return <option key={t} value={t}>{t.replace(/_/g, " ")} · {d?.status ?? "missing"}</option>; })}</select>}>
        <DocumentViewer versionId={v.semantic_version} type={doc} />
      </Card>
      <Card title="Governance copilot">
        <Copilot id={v.semantic_version} />
      </Card>
    </div>
  );
}
