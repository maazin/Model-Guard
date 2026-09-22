import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useParams } from "react-router-dom";
import { useCurrentUser, useVersion } from "../lib/hooks";
import { STATIC_DEMO, post } from "../lib/api";
import { Badge, Card, ErrorBox, Glossary, Loading, PageHeader, Term, fmtDate } from "../components/ui";
import { DocumentViewer } from "../components/DocumentViewer";

const DOC_TYPES: [string, string][] = [
  ["intended_use", "Intended use"],
  ["model_card", "Model card"],
  ["data_lineage", "Data lineage and dictionary"],
  ["validation_report", "Validation report"],
  ["monitoring_plan", "Monitoring plan"],
  ["control_matrix", "Control matrix"],
  ["risk_assessment", "Risk assessment"],
  ["change_log", "Change log"],
];
const CHECK_LABEL: Record<string, string> = {
  dataset_lineage: "Data source and lineage",
  model_documentation: "Documentation",
  validation: "Validation results",
  monitoring_plan: "Monitoring plan",
  fairness_assessment: "Fairness assessment",
  controls: "Controls",
  security: "Security checks",
  sign_off: "Reviewer sign-off",
};

function useAction(id: string) {
  const qc = useQueryClient();
  const [error, setError] = useState<any>(null);
  const m = useMutation({
    mutationFn: ({ path, body }: { path: string; body?: unknown }) => post(`/api/v1/model-versions/${id}${path}`, body),
    onSuccess: () => { setError(null); qc.invalidateQueries(); },
    onError: setError,
  });
  return { m, error };
}

function EvidenceAssistant({ id }: { id: string }) {
  const [question, setQuestion] = useState(`What evidence is missing before ${id} can move to approved?`);
  const m = useMutation({ mutationFn: () => post(`/api/v1/model-versions/${id}/copilot/query`, { question }) });
  const r = m.data;
  return (
    <div className="space-y-3">
      <p className="muted text-sm">
        Answers are drawn only from this version's own documents and readiness results, and every answer cites the document section it came from. The assistant cannot approve
        anything and never sees borrower records.{STATIC_DEMO && " In this demonstration the answer is prepared for the question shown."}
      </p>
      <textarea className="field" rows={2} value={question} onChange={(e) => setQuestion(e.target.value)} aria-label="Question" data-testid="copilot-question" />
      <button className="btn btn-primary" onClick={() => m.mutate()} disabled={m.isPending || !question.trim()} data-testid="copilot-ask">Check the evidence</button>
      {m.error && <ErrorBox error={m.error} />}
      {r && (
        <div className="space-y-3 border-t pt-3 text-sm hairline" data-testid="copilot-answer">
          <p>{r.response.answer}</p>
          {r.response.missing_requirements.filter((x: any) => x.status !== "present").length > 0 && (
            <ul className="space-y-2">
              {r.response.missing_requirements.filter((x: any) => x.status !== "present").map((x: any) => (
                <li key={x.requirement}>
                  <div className="flex items-center gap-2"><Badge value="fail" label={x.status === "missing" ? "Missing" : "Incomplete"} /><strong>{x.requirement}</strong></div>
                  {x.evidence.length > 0 && <ul className="muted mt-1 list-disc pl-6 text-[13px]">{x.evidence.map((e: string) => <li key={e}>{e}</li>)}</ul>}
                </li>
              ))}
            </ul>
          )}
          <div className="faint text-[13px]">
            <span>Citations: </span>
            {r.response.citations.map((c: any) => <span key={`${c.document_id}-${c.section}`} className="mr-2 inline-block rounded px-1.5 py-0.5" style={{ background: "var(--surface-2)" }}>{c.document_id.split("-")[0].replace(/_/g, " ")} › {c.section}</span>)}
          </div>
          <p className="faint text-[13px]">Source: {r.provider === "rule_based" ? "rule-based check, no external service" : r.provider} · confidence {r.response.confidence}. Not an approval authority.</p>
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
  const lede = failing.length === 0
    ? "Every requirement has evidence on file."
    : failing.length === 1 && failing[0].check_name === "sign_off"
      ? "All evidence is on file. The only outstanding item is a reviewer's decision."
      : `${failing.length} of ${v.readiness.length} requirements still lack evidence. Each gap is listed by name below.`;
  return (
    <div className="space-y-8">
      <PageHeader title="Approval and evidence" lede={lede} badges={<Badge value={v.state} />} />
      {error && <ErrorBox error={error} />}
      <div className="grid gap-4 lg:grid-cols-[1fr_340px]">
        <Card title={<><Term k="readiness">Readiness checks</Term> · {v.readiness.length - failing.length} of {v.readiness.length} met</>}>
          <ul className="space-y-2" data-testid="readiness-list">
            {v.readiness.map((c) => (
              <li key={c.check_name} className="rounded-xl px-3 py-2.5" style={{ background: "var(--surface-2)" }}>
                <div className="flex items-center justify-between gap-2 text-sm">
                  <span className="font-medium">{CHECK_LABEL[c.check_name] ?? c.check_name}</span>
                  <Badge value={c.status} />
                </div>
                {c.missing.length > 0 && <ul className="muted mt-1.5 list-disc pl-5 text-[13px]" data-testid="missing-evidence">{c.missing.map((mm) => <li key={mm}>{mm}</li>)}</ul>}
              </li>
            ))}
          </ul>
        </Card>
        <div className="space-y-4">
          <Card title="Your decision" subtitle={`Viewing as ${role.replace(/_/g, " ")}.`}>
            <div className="space-y-2 text-sm">
              {isDS && (v.state === "DRAFT" || v.state === "VALIDATED") && <button className="btn w-full" onClick={() => m.mutate({ path: "/validate" })} disabled={m.isPending}>Run validation</button>}
              {isDS && v.state === "VALIDATED" && <button className="btn btn-primary w-full" onClick={() => m.mutate({ path: "/submit-review" })} disabled={m.isPending} data-testid="submit-review">Submit for review</button>}
              {isDS && v.state === "REJECTED" && <button className="btn w-full" onClick={() => m.mutate({ path: "/reopen" })} disabled={m.isPending}>Reopen as draft</button>}
              {isReviewer && v.state === "PENDING_REVIEW" && (
                <div className="space-y-2" data-testid="decision-form">
                  <label className="muted text-xs" htmlFor="rationale">Reason for the decision (kept permanently in the audit log)</label>
                  <textarea id="rationale" className="field" rows={3} value={rationale} onChange={(e) => setRationale(e.target.value)} placeholder="Why are you approving or rejecting?" />
                  <div className="flex gap-2">
                    <button className="btn btn-primary flex-1" disabled={m.isPending || rationale.length < 3} onClick={() => m.mutate({ path: "/decision", body: { decision: "approve", rationale } })} data-testid="approve">Approve</button>
                    <button className="btn btn-danger flex-1" disabled={m.isPending || rationale.length < 3} onClick={() => m.mutate({ path: "/decision", body: { decision: "reject", rationale } })} data-testid="reject">Reject</button>
                  </div>
                </div>
              )}
              {isReviewer && (v.state === "APPROVED" || v.state === "MONITORING") && (
                <div className="space-y-2">
                  <input className="field" placeholder="Reason for retiring this version" value={reason} onChange={(e) => setReason(e.target.value)} />
                  <button className="btn w-full" disabled={m.isPending || reason.length < 3} onClick={() => m.mutate({ path: "/retire", body: { reason } })}>Retire this version</button>
                </div>
              )}
              {!isDS && !isReviewer && <p className="muted">Risk leaders have read-only access. Choose another role at the top right to act.</p>}
              {isDS && v.state === "PENDING_REVIEW" && <p className="muted">Waiting for the reviewer. Documents and controls are frozen until a decision is made.</p>}
              {isReviewer && (v.state === "DRAFT" || v.state === "VALIDATED") && <p className="muted">Nothing to decide until the data scientist submits this version for review.</p>}
              {isReviewer && v.state === "REJECTED" && <p className="muted">Rejected. The data scientist can reopen it as a draft after addressing the reason.</p>}
            </div>
          </Card>
          <Card title="Decisions so far">
            {v.decisions.length === 0 ? <p className="muted text-sm">No reviewer decision yet.</p> : (
              <ul className="space-y-3 text-sm">{v.decisions.map((d) => <li key={d.id}><div className="flex items-center gap-2"><Badge value={d.decision} /><span className="muted">{d.reviewer_id.replace(/_/g, " ")} · {fmtDate(d.decided_at)}</span></div><div className="mt-1">{d.rationale}</div></li>)}</ul>
            )}
          </Card>
        </div>
      </div>
      <Card title={<><Term k="controls">Controls</Term> · {v.controls.length}</>} subtitle="The safeguards around this model. Each needs an owner, a frequency and evidence that it has been tested.">
        {v.controls.length === 0 ? <p className="muted text-sm">No controls recorded yet.</p> : (
          <div className="overflow-auto">
            <table className="data"><thead><tr><th>Control</th><th>Owner</th><th>How often</th><th>Status</th><th>Evidence</th></tr></thead>
              <tbody>{v.controls.map((c) => <tr key={c.id}><td><div className="font-medium">{c.control_name}</div><div className="faint text-xs">{c.description}</div></td><td>{c.owner.replace(/_/g, " ")}</td><td>{c.frequency}</td><td><Badge value={c.status === "planned" ? "fail" : "pass"} label={c.status} /></td><td className="text-xs">{c.test_evidence}<div className="faint"><code>{c.evidence_uri}</code></div></td></tr>)}</tbody>
            </table>
          </div>
        )}
      </Card>
      <Card
        title="Documents"
        subtitle="Eight documents are kept for every version. A document counts as complete only when every required section is filled in."
        actions={<select className="field w-auto" value={doc} onChange={(e) => setDoc(e.target.value)} aria-label="Document">{DOC_TYPES.map(([t, label]) => { const d = v.documents.find((x) => x.type === t); return <option key={t} value={t}>{label} · {d?.status ?? "missing"}</option>; })}</select>}
      >
        <DocumentViewer versionId={v.semantic_version} type={doc} />
      </Card>
      <Card title="Ask what evidence is missing">
        <EvidenceAssistant id={v.semantic_version} />
      </Card>
      <Glossary keys={["readiness", "controls", "modelCard", "lifecycle", "audit"]} />
    </div>
  );
}
