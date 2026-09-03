import { FormEvent, useState } from "react";
import { api, ChangeRequest } from "../api/client";

const EXAMPLE_CR = {
  application: "SanofiOrders",
  service_now_id: "CHG0012345",
  summary: "Add order-approval threshold business rule",
  description:
    "Modify the application to support a new business rule for order approval above a " +
    "specified threshold. Orders below the threshold amount should be automatically " +
    "approved without requiring manual Tech Lead / Finance sign-off; orders at or above " +
    "the threshold continue to require manual approval as today.",
};

export function Intake({ onCreated }: { onCreated: (cr: ChangeRequest, startAnalysis: boolean) => void }) {
  const [form, setForm] = useState(EXAMPLE_CR);
  const [priority, setPriority] = useState("Medium");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const cr = await api.createChangeRequest({ ...form, priority });
      onCreated(cr, true);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page">
      <h1>New Change Request</h1>
      <form className="intake-form" onSubmit={handleSubmit}>
        <label>
          Application
          <input
            value={form.application}
            onChange={(e) => setForm({ ...form, application: e.target.value })}
            required
          />
        </label>
        <label>
          ServiceNow CR ID (optional)
          <input
            value={form.service_now_id}
            onChange={(e) => setForm({ ...form, service_now_id: e.target.value })}
          />
        </label>
        <label>
          Summary
          <input
            value={form.summary}
            onChange={(e) => setForm({ ...form, summary: e.target.value })}
            required
          />
        </label>
        <label>
          Description
          <textarea
            rows={6}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            required
          />
        </label>
        <label>
          Priority
          <select value={priority} onChange={(e) => setPriority(e.target.value)}>
            <option>Low</option>
            <option>Medium</option>
            <option>High</option>
            <option>Critical</option>
          </select>
        </label>
        {error && <p className="error-text">{error}</p>}
        <button className="btn btn-primary" type="submit" disabled={submitting}>
          {submitting ? "Creating..." : "Create & Run Analysis"}
        </button>
      </form>
    </div>
  );
}
