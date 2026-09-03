import { useState } from "react";
import { api } from "../api/client";

export function ApproveEditReject({ runId }: { runId: number }) {
  const [comment, setComment] = useState("");
  const [lastDecision, setLastDecision] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit(decision: "Accepted" | "Edited" | "Rejected") {
    setSubmitting(true);
    try {
      await api.submitFeedback(runId, { user: "tech.lead@cognizant.com", decision, comment });
      setLastDecision(decision);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="approval-box">
      <h3>Tech Lead Review</h3>
      <textarea
        placeholder="Optional comment / edits to the AI findings..."
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        rows={3}
      />
      <div className="approval-actions">
        <button disabled={submitting} className="btn btn-accept" onClick={() => submit("Accepted")}>
          Accept
        </button>
        <button disabled={submitting} className="btn btn-edit" onClick={() => submit("Edited")}>
          Accept with edits
        </button>
        <button disabled={submitting} className="btn btn-reject" onClick={() => submit("Rejected")}>
          Reject
        </button>
      </div>
      {lastDecision && <p className="approval-confirm">Recorded: {lastDecision}</p>}
    </div>
  );
}
