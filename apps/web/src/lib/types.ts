export type State = "DRAFT" | "VALIDATED" | "PENDING_REVIEW" | "APPROVED" | "MONITORING" | "REJECTED" | "RETIRED";

export interface MetricValue { value: number; lower_ci?: number; upper_ci?: number }
export interface ModelVersion {
  id: string; semantic_version: string; training_run_id: string; state: State; artifact_uri: string;
  model_type: "baseline" | "champion"; owner: string; description: string; retirement_reason: string | null;
  created_at: string; updated_at: string;
}
export interface Readiness { check_name: string; status: "pass" | "fail"; missing: string[]; evidence: Record<string, any> }
export interface Document { id: string; type: string; version: number; content_hash: string; status: string; path: string; updated_at: string }
export interface Control { id: string; control_name: string; description: string; owner: string; frequency: string; status: string; evidence_uri: string; test_evidence: string }
export interface Decision { id: string; reviewer_id: string; decision: string; rationale: string; decided_at: string }
export interface Alert {
  id: string; monitoring_batch_id: string; type: string; severity: "low" | "medium" | "high"; status: "open" | "investigating" | "resolved";
  title: string; detail_json: Record<string, any>; owner: string; due_date: string; investigation_note: string | null; resolution_note: string | null; created_at: string;
}
export interface AuditEvent { id: number; actor_id: string; action: string; entity_type: string; entity_id: string; before_json: any; after_json: any; occurred_at: string; previous_hash: string; event_hash: string }
export interface Metric { scope: string; metric_name: string; metric_value: number; lower_ci: number | null; upper_ci: number | null; batch_id: string | null }
export interface VersionDetail extends ModelVersion {
  training_run: any; snapshot: any; source: any; metrics: Metric[]; artifacts: Record<string, any>; documents: Document[];
  controls: Control[]; readiness: Readiness[]; decisions: Decision[]; alerts: Alert[]; audit_events: AuditEvent[]; narrative: Record<string, string>;
}
export interface MonitoringBatch { id: string; snapshot_id: string; as_of_date: string; status: string; labels_available: boolean; results_json: any; created_at: string }
export interface Monitoring { model_version: string; state: State; thresholds: Record<string, number>; holdout_auc: number | null; batches: MonitoringBatch[]; alerts: Alert[] }
export interface ExecutiveSummary {
  model_version: string; model_version_id: string; state: State; model_type: string; purpose: string; limits: string[];
  health: "healthy" | "watch" | "at_risk" | "retired"; holdout: Record<string, MetricValue>; comparator: Record<string, MetricValue>;
  latest_batch: { as_of_date: string; status: string; auc: number | null; labels_available: boolean } | null; batches_evaluated: number;
  alerts: { open: number; high: number; resolved: number }; readiness: { passed: number; total: number; failing: string[] };
  top_risks: string[]; recommendation: string; next_action: string;
}
