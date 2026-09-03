import { useEffect, useState } from "react";
import { CostBand, EffortSettings, api } from "../api/client";

export function Settings({ onBack }: { onBack: () => void }) {
  const [settings, setSettings] = useState<EffortSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api
      .getEffortSettings()
      .then(setSettings)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }, []);

  function updateBand(index: number, field: keyof CostBand, value: string) {
    if (!settings) return;
    const bands = [...settings.cost_bands];
    bands[index] = {
      ...bands[index],
      [field]: field === "label" ? value : Number(value),
    };
    setSettings({ ...settings, cost_bands: bands });
  }

  async function save() {
    if (!settings) return;
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const updated = await api.updateEffortSettings(settings);
      setSettings(updated);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="page">Loading settings...</div>;
  if (!settings) return <div className="page error-text">{error ?? "Could not load settings."}</div>;

  return (
    <div className="page">
      <div className="page-header">
        <button className="btn btn-link" onClick={onBack}>
          ← Dashboard
        </button>
      </div>
      <h1>Effort &amp; Cost Settings</h1>
      <p className="cr-meta">
        These values drive every analysis run's effort estimate and EUR cost. Update them
        periodically to reflect current rates — changes apply to new analysis runs only.
      </p>

      <h2>Overhead defaults (days, 8h = 1 day)</h2>
      <div className="settings-grid">
        <label>
          Change Management (SNOW)
          <input
            type="number"
            step="0.05"
            min="0"
            value={settings.change_management_default_days}
            onChange={(e) =>
              setSettings({ ...settings, change_management_default_days: Number(e.target.value) })
            }
          />
        </label>
        <label>
          Enhancement / Project Coordination (% of Analysis+Build+Testing+UAT)
          <input
            type="number"
            step="1"
            min="0"
            max="100"
            value={Math.round(settings.enhancement_coordination_percent * 100)}
            onChange={(e) =>
              setSettings({ ...settings, enhancement_coordination_percent: Number(e.target.value) / 100 })
            }
          />
        </label>
      </div>

      <h2>Cost bands (EUR)</h2>
      <p className="cr-meta">
        First band where total effort days &lt; "Upper bound" applies. Totals at or above the
        last band's upper bound show "Manual costing required."
      </p>
      <table className="settings-table">
        <thead>
          <tr>
            <th>Label</th>
            <th>Upper bound (days, exclusive)</th>
            <th>Cost (EUR)</th>
          </tr>
        </thead>
        <tbody>
          {settings.cost_bands
            .slice()
            .sort((a, b) => a.upper_bound_days - b.upper_bound_days)
            .map((band, i) => (
              <tr key={i}>
                <td>
                  <input
                    value={band.label}
                    onChange={(e) => updateBand(i, "label", e.target.value)}
                  />
                </td>
                <td>
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    value={band.upper_bound_days}
                    onChange={(e) => updateBand(i, "upper_bound_days", e.target.value)}
                  />
                </td>
                <td>
                  <input
                    type="number"
                    step="1"
                    min="0"
                    value={band.cost_eur}
                    onChange={(e) => updateBand(i, "cost_eur", e.target.value)}
                  />
                </td>
              </tr>
            ))}
        </tbody>
      </table>

      {error && <p className="error-text">{error}</p>}
      {saved && <p className="approval-confirm">Settings saved.</p>}
      <button className="btn btn-primary" onClick={save} disabled={saving}>
        {saving ? "Saving..." : "Save Settings"}
      </button>
    </div>
  );
}
