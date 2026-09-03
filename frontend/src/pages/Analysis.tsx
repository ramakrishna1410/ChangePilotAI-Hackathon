import { useEffect, useState } from "react";
import { AnalysisRun, ChangeRequest, api } from "../api/client";
import { EvidenceBadges } from "../components/EvidencePanel";
import { ApproveEditReject } from "../components/ApproveEditReject";

type Tab = "summary" | "impact" | "dependencies" | "risk" | "effort" | "regression" | "validation";

export function Analysis({
  cr,
  autoStart,
  onBack,
}: {
  cr: ChangeRequest;
  autoStart: boolean;
  onBack: () => void;
}) {
  const [run, setRun] = useState<AnalysisRun | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("summary");

  async function startAnalysis() {
    setLoading(true);
    setError(null);
    try {
      const result = await api.startAnalysis(cr.id);
      setRun(result);
      if (result.status === "Failed") {
        setError(result_error(result));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  function result_error(r: AnalysisRun): string {
    return "Analysis failed. Check the backend logs / OPENAI_API_KEY configuration.";
  }

  useEffect(() => {
    if (autoStart) {
      startAnalysis();
    } else {
      api.listAnalysisRuns(cr.id).then((runs) => {
        if (runs.length > 0) setRun(runs[0]);
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cr.id]);

  const result = run?.result;

  return (
    <div className="page">
      <div className="page-header">
        <button className="btn btn-link" onClick={onBack}>
          ← Dashboard
        </button>
        <button className="btn btn-secondary" onClick={startAnalysis} disabled={loading}>
          {loading ? "Analyzing..." : "Re-run Analysis"}
        </button>
      </div>
      <h1>{cr.summary}</h1>
      <p className="cr-meta">
        {cr.application} · Priority: {cr.priority}
        {cr.service_now_id ? ` · ${cr.service_now_id}` : ""}
      </p>

      {loading && <p>Running orchestrator: requirement → impact (RAG) → dependencies → risk/effort → regression → validation...</p>}
      {error && <p className="error-text">{error}</p>}

      {result && (
        <>
          <div className="tabs">
            {(["summary", "impact", "dependencies", "risk", "effort", "regression", "validation"] as Tab[]).map(
              (t) => (
                <button key={t} className={`tab ${tab === t ? "tab-active" : ""}`} onClick={() => setTab(t)}>
                  {t === "validation" ? `Needs Validation (${result.needs_validation.length})` : t}
                </button>
              )
            )}
          </div>

          {tab === "summary" && (
            <div className="tab-panel">
              <h2>Requirement Summary</h2>
              <p>
                <strong>Objective:</strong> {result.requirement.objective}
              </p>
              <p>
                <strong>Scope:</strong> {result.requirement.scope}
              </p>
              {result.requirement.constraints.length > 0 && (
                <>
                  <strong>Constraints:</strong>
                  <ul>
                    {result.requirement.constraints.map((c, i) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                </>
              )}
              {result.requirement.acceptance_criteria.length > 0 && (
                <>
                  <strong>Acceptance Criteria:</strong>
                  <ul>
                    {result.requirement.acceptance_criteria.map((c, i) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          )}

          {tab === "impact" && (
            <div className="tab-panel">
              <h2>Impacted Components ({result.impacted_items.length})</h2>
              {result.impacted_items.map((item, i) => (
                <div key={i} className="finding-card">
                  <div className="finding-header">
                    <span className={`badge badge-level-${item.impact_level.toLowerCase().replace(/ /g, "-")}`}>
                      {item.impact_level}
                    </span>
                    <strong>
                      {item.type}: {item.name}
                    </strong>
                    <span className="confidence">conf {Math.round(item.confidence * 100)}%</span>
                  </div>
                  <p className="finding-path">{item.path}</p>
                  <p>{item.reason}</p>
                  <EvidenceBadges refs={item.evidence_refs} />
                </div>
              ))}
            </div>
          )}

          {tab === "dependencies" && (
            <div className="tab-panel">
              <h2>Dependencies ({result.dependencies.length})</h2>
              {result.dependencies.map((dep, i) => (
                <div key={i} className="finding-card">
                  <strong>
                    {dep.source} → {dep.target}
                  </strong>{" "}
                  <span className="badge">{dep.dependency_type}</span>
                  <EvidenceBadges refs={dep.evidence_ref} />
                </div>
              ))}
            </div>
          )}

          {tab === "risk" && (
            <div className="tab-panel">
              <h2>Risks ({result.risks.length})</h2>
              {result.risks.map((risk, i) => (
                <div key={i} className="finding-card">
                  <div className="finding-header">
                    <span className={`badge badge-severity-${risk.severity.toLowerCase()}`}>{risk.severity}</span>
                    <strong>{risk.risk}</strong>
                  </div>
                  <p>{risk.rationale}</p>
                  <p className="mitigation">
                    <strong>Mitigation:</strong> {risk.mitigation}
                  </p>
                  <EvidenceBadges refs={risk.evidence_ref} />
                </div>
              ))}
            </div>
          )}

          {tab === "effort" && (
            <div className="tab-panel">
              <h2>Effort Estimate</h2>
              <div className="finding-card">
                <p className="effort-hours">{result.effort_estimate.analysis_hours} hours</p>
                <p>
                  Complexity: <strong>{result.effort_estimate.complexity}</strong> · Confidence:{" "}
                  {Math.round(result.effort_estimate.confidence * 100)}%
                </p>
                <p>{result.effort_estimate.rationale}</p>
              </div>
            </div>
          )}

          {tab === "regression" && (
            <div className="tab-panel">
              <h2>Regression Scenarios ({result.test_scenarios.length})</h2>
              {result.test_scenarios.map((s, i) => (
                <div key={i} className="finding-card">
                  <div className="finding-header">
                    <span className="badge">{s.type}</span>
                    <span className={`badge badge-priority-${s.priority.toLowerCase()}`}>{s.priority}</span>
                    <strong>{s.impacted_area}</strong>
                  </div>
                  <p>{s.scenario}</p>
                  <EvidenceBadges refs={s.evidence_ref} />
                </div>
              ))}
            </div>
          )}

          {tab === "validation" && (
            <div className="tab-panel">
              <h2>Needs Validation ({result.needs_validation.length})</h2>
              {result.needs_validation.length === 0 && <p>All material findings are evidence-backed.</p>}
              {result.needs_validation.map((f, i) => (
                <div key={i} className="finding-card finding-warning">
                  <strong>{f.item_description}</strong>
                  <p>{f.issue}</p>
                </div>
              ))}
            </div>
          )}

          {run && <ApproveEditReject runId={run.id} />}
        </>
      )}
    </div>
  );
}
