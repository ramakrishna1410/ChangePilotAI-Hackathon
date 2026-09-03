const BASE_URL = "http://localhost:8000";

export interface ChangeRequest {
  id: number;
  service_now_id?: string | null;
  application: string;
  summary: string;
  description: string;
  priority: string;
  status: string;
  created_date: string;
}

export interface EvidenceRef {
  chunk_id: string;
  source_path: string;
  symbol?: string | null;
}

export interface ImpactItem {
  type: string;
  name: string;
  path: string;
  impact_level: string;
  reason: string;
  evidence_refs: EvidenceRef[];
  confidence: number;
}

export interface Dependency {
  source: string;
  target: string;
  dependency_type: string;
  evidence_ref?: EvidenceRef | null;
}

export interface RiskItem {
  risk: string;
  severity: string;
  rationale: string;
  evidence_ref?: EvidenceRef | null;
  mitigation: string;
}

export interface EffortEstimate {
  analysis_design_days: number;
  build_days: number;
  testing_sit_days: number;
  uat_support_days: number;
  change_management_days: number;
  enhancement_coordination_days: number;
  total_days: number;
  complexity: string;
  confidence: number;
  rationale: string;
  cost_status: "Computed" | "ManualCostingRequired";
  cost_eur?: number | null;
  cost_band_label?: string | null;
}

export interface CostBand {
  label: string;
  upper_bound_days: number;
  cost_eur: number;
}

export interface EffortSettings {
  change_management_default_days: number;
  enhancement_coordination_default_days: number;
  cost_bands: CostBand[];
}

export interface TestScenario {
  scenario: string;
  type: string;
  priority: string;
  impacted_area: string;
  evidence_ref?: EvidenceRef | null;
}

export interface ValidationFinding {
  item_description: string;
  issue: string;
}

export interface RequirementSummary {
  objective: string;
  scope: string;
  constraints: string[];
  acceptance_criteria: string[];
  affected_application: string;
}

export interface AnalysisResult {
  requirement: RequirementSummary;
  impacted_items: ImpactItem[];
  dependencies: Dependency[];
  risks: RiskItem[];
  effort_estimate: EffortEstimate;
  test_scenarios: TestScenario[];
  needs_validation: ValidationFinding[];
}

export type ReviewStatus = "NotReviewed" | "Approved" | "ApprovedEdited" | "Rejected";

export interface AnalysisRun {
  id: number;
  change_request_id: number;
  model: string;
  status: "Pending" | "Running" | "Completed" | "Failed";
  started_at: string;
  completed_at?: string | null;
  result?: AnalysisResult | null;
  ai_original_result?: AnalysisResult | null;
  review_status: ReviewStatus;
  decided_by?: string | null;
  decided_at?: string | null;
  decision_comment?: string | null;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listChangeRequests: () => request<ChangeRequest[]>("/change-requests"),
  createChangeRequest: (payload: {
    application: string;
    summary: string;
    description: string;
    priority: string;
    service_now_id?: string;
  }) =>
    request<ChangeRequest>("/change-requests", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  startAnalysis: (crId: number) =>
    request<AnalysisRun>(`/analysis-runs/${crId}`, { method: "POST" }),
  getAnalysisRun: (runId: number) => request<AnalysisRun>(`/analysis-runs/${runId}`),
  listAnalysisRuns: (crId?: number) =>
    request<AnalysisRun[]>(`/analysis-runs${crId ? `?change_request_id=${crId}` : ""}`),
  submitFeedback: (
    runId: number,
    payload: { user: string; decision: "Accepted" | "Edited" | "Rejected"; comment?: string; edited_result?: AnalysisResult }
  ) =>
    request<AnalysisRun>(`/analysis-runs/${runId}/feedback`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getEffortSettings: () => request<EffortSettings>("/settings/effort"),
  updateEffortSettings: (payload: EffortSettings) =>
    request<EffortSettings>("/settings/effort", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
};
