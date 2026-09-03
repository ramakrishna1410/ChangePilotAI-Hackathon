import { EvidenceRef } from "../api/client";

export function EvidenceBadges({ refs }: { refs?: EvidenceRef[] | EvidenceRef | null }) {
  const list = !refs ? [] : Array.isArray(refs) ? refs : [refs];
  if (list.length === 0) {
    return <span className="badge badge-warning">No evidence cited</span>;
  }
  return (
    <div className="evidence-badges">
      {list.map((ref) => (
        <span key={ref.chunk_id} className="badge badge-evidence" title={ref.chunk_id}>
          {ref.source_path}
          {ref.symbol ? ` · ${ref.symbol}` : ""}
        </span>
      ))}
    </div>
  );
}
