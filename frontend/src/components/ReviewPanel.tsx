import { useEffect, useState } from "react";
import { AnalysisResult, AnalysisRun, CostBand, EffortSettings, ImpactItem, api } from "../api/client";

const IMPACT_LEVELS = ["Direct", "Indirect", "Potentially Related"];

function computeCost(totalDays: number, bands: CostBand[]) {
  const sorted = [...bands].sort((a, b) => a.upper_bound_days - b.upper_bound_days);
  for (const band of sorted) {
    if (totalDays < band.upper_bound_days) {
      return { cost_status: "Computed" as const, cost_eur: band.cost_eur, cost_band_label: band.label };
    }
  }
  return { cost_status: "ManualCostingRequired" as const, cost_eur: null, cost_band_label: null };
}

function EditForm({
  original,
  settings,
  onChange,
}: {
  original: AnalysisResult;
  settings: EffortSettings;
  onChange: (result: AnalysisResult) => void;
}) {
  const [effort, setEffort] = useState({ ...original.effort_estimate });
  const [items, setItems] = useState<ImpactItem[]>(original.impacted_items.map((i) => ({ ...i })));

  const totalDays =
    effort.analysis_design_days +
    effort.build_days +
    effort.testing_sit_days +
    effort.uat_support_days +
    effort.change_management_days +
    effort.enhancement_coordination_days;
  const cost = computeCost(totalDays, settings.cost_bands);

  useEffect(() => {
    onChange({
      ...original,
      impacted_items: items,
      effort_estimate: {
        ...effort,
        total_days: Math.round(totalDays * 100) / 100,
        ...cost,
      },
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [effort, items]);

  function setDays(field: keyof typeof effort, value: string) {
    setEffort({ ...effort, [field]: Number(value) || 0 });
  }

  return (
    <div className="edit-form">
      <h4>Effort (days, 8h = 1 day)</h4>
      {(
        [
          ["analysis_design_days", "Analysis & Design"],
          ["build_days", "Build (Dev & Unit Testing)"],
          ["testing_sit_days", "Testing (SIT)"],
          ["uat_support_days", "UAT Support"],
          ["change_management_days", "Change Management (SNOW)"],
          ["enhancement_coordination_days", "Enhancement/Project Coordination"],
        ] as const
      ).map(([field, label]) => (
        <label key={field}>
          {label}
          <input
            type="number"
            step="0.05"
            min="0"
            value={effort[field]}
            onChange={(e) => setDays(field, e.target.value)}
          />
        </label>
      ))}
      <p>
        <strong>Total: {Math.round(totalDays * 100) / 100} days</strong> —{" "}
        {cost.cost_status === "Computed" ? `€${cost.cost_eur} (${cost.cost_band_label})` : "Manual costing required"}
      </p>

      {items.length > 0 && (
        <>
          <h4>Impact levels</h4>
          {items.map((item, i) => (
            <div key={i} className="edit-row">
              <span style={{ flex: 1 }}>
                {item.type}: {item.name}
              </span>
              <select
                value={item.impact_level}
                onChange={(e) => {
                  const next = [...items];
                  next[i] = { ...next[i], impact_level: e.target.value as ImpactItem["impact_level"] };
                  setItems(next);
                }}
              >
                {IMPACT_LEVELS.map((l) => (
                  <option key={l} value={l}>
                    {l}
                  </option>
                ))}
              </select>
            </div>
          ))}
        </>
      )}
    </div>
  );
}

export function ReviewPanel({ run, onUpdated }: { run: AnalysisRun; onUpdated: (run: AnalysisRun) => void }) {
  const [comment, setComment] = useState("");
  const [editing, setEditing] = useState(false);
  const [editedResult, setEditedResult] = useState<AnalysisResult | null>(null);
  const [settings, setSettings] = useState<EffortSettings | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (editing && !settings) {
      api.getEffortSettings().then(setSettings);
    }
  }, [editing, settings]);

  if (run.review_status !== "NotReviewed") {
    const cls =
      run.review_status === "Rejected"
        ? "review-banner-rejected"
        : run.review_status === "ApprovedEdited"
          ? "review-banner-approvededited"
          : "review-banner-approved";
    return (
      <div className={`review-banner ${cls}`}>
        <strong>{run.review_status === "ApprovedEdited" ? "Approved (Edited)" : run.review_status}</strong>
        {run.decided_by && (
          <p>
            by {run.decided_by} {run.decided_at ? `on ${new Date(run.decided_at).toLocaleString()}` : ""}
          </p>
        )}
        {run.decision_comment && <p>"{run.decision_comment}"</p>}
        {run.review_status === "Rejected" && (
          <p className="cr-meta">This run is closed. Start a new analysis run to try again.</p>
        )}
      </div>
    );
  }

  async function submit(decision: "Accepted" | "Edited" | "Rejected") {
    setSubmitting(true);
    setError(null);
    try {
      const payload: Parameters<typeof api.submitFeedback>[1] = {
        user: "tech.lead@cognizant.com",
        decision,
        comment,
      };
      if (decision === "Edited") {
        if (!editedResult) {
          setError("Edit form did not load yet — please wait a moment and try again.");
          setSubmitting(false);
          return;
        }
        payload.edited_result = editedResult;
      }
      const updated = await api.submitFeedback(run.id, payload);
      onUpdated(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="approval-box">
      <h3>Tech Lead Review</h3>
      <textarea
        placeholder="Optional comment..."
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        rows={3}
      />

      {editing && run.result && (
        settings ? (
          <EditForm original={run.result} settings={settings} onChange={setEditedResult} />
        ) : (
          <p>Loading settings...</p>
        )
      )}

      {error && <p className="error-text">{error}</p>}

      <div className="approval-actions">
        {!editing && (
          <>
            <button disabled={submitting} className="btn btn-accept" onClick={() => submit("Accepted")}>
              Accept
            </button>
            <button disabled={submitting} className="btn btn-edit" onClick={() => setEditing(true)}>
              Accept with edits
            </button>
            <button disabled={submitting} className="btn btn-reject" onClick={() => submit("Rejected")}>
              Reject
            </button>
          </>
        )}
        {editing && (
          <>
            <button disabled={submitting || !editedResult} className="btn btn-edit" onClick={() => submit("Edited")}>
              {submitting ? "Saving..." : "Save & Accept with Edits"}
            </button>
            <button disabled={submitting} className="btn btn-secondary" onClick={() => setEditing(false)}>
              Cancel
            </button>
          </>
        )}
      </div>
    </div>
  );
}
