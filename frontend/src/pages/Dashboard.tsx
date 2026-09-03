import { useEffect, useState } from "react";
import { api, ChangeRequest } from "../api/client";

export function Dashboard({
  onSelectCr,
  onNewCr,
  onSettings,
}: {
  onSelectCr: (cr: ChangeRequest) => void;
  onNewCr: () => void;
  onSettings: () => void;
}) {
  const [crs, setCrs] = useState<ChangeRequest[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .listChangeRequests()
      .then(setCrs)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <h1>ChangePilot AI — Dashboard</h1>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn btn-secondary" onClick={onSettings}>
            Settings
          </button>
          <button className="btn btn-primary" onClick={onNewCr}>
            + New Change Request
          </button>
        </div>
      </div>
      {loading && <p>Loading...</p>}
      {!loading && crs.length === 0 && (
        <p className="empty-state">No change requests yet. Create one to run an analysis.</p>
      )}
      <div className="cr-list">
        {crs.map((cr) => (
          <div key={cr.id} className="cr-card" onClick={() => onSelectCr(cr)}>
            <div className="cr-card-header">
              <strong>{cr.summary}</strong>
              <span className={`badge badge-status-${cr.status.toLowerCase()}`}>{cr.status}</span>
            </div>
            <div className="cr-card-meta">
              {cr.application} · Priority: {cr.priority}
              {cr.service_now_id ? ` · ${cr.service_now_id}` : ""}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
