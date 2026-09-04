def test_get_effort_settings_returns_seeded_defaults(client):
    resp = client.get("/settings/effort")
    assert resp.status_code == 200
    body = resp.json()
    assert body["change_management_default_days"] == 0.50
    assert body["enhancement_coordination_percent"] == 0.10
    assert len(body["cost_bands"]) == 6


def test_put_effort_settings_persists_and_sorts_bands(client):
    payload = {
        "change_management_default_days": 0.75,
        "enhancement_coordination_percent": 0.15,
        "cost_bands": [
            {"label": "b", "upper_bound_days": 5, "cost_eur": 500},
            {"label": "a", "upper_bound_days": 1, "cost_eur": 100},
        ],
        "changed_by": "tester@x.com",
    }
    resp = client.put("/settings/effort", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["change_management_default_days"] == 0.75
    assert body["enhancement_coordination_percent"] == 0.15
    assert [b["label"] for b in body["cost_bands"]] == ["a", "b"]

    refetched = client.get("/settings/effort").json()
    assert refetched["change_management_default_days"] == 0.75


def test_put_effort_settings_records_audit_history(client):
    before = client.get("/settings/effort/history").json()

    client.put(
        "/settings/effort",
        json={
            "change_management_default_days": 0.6,
            "enhancement_coordination_percent": 0.12,
            "cost_bands": [{"label": "a", "upper_bound_days": 1, "cost_eur": 150}],
            "changed_by": "tech.lead@cognizant.com",
        },
    )

    after = client.get("/settings/effort/history").json()
    assert len(after) == len(before) + 1
    latest = after[0]  # ordered newest first
    assert latest["changed_by"] == "tech.lead@cognizant.com"
    assert latest["new"]["change_management_default_days"] == 0.6
    assert latest["previous"]["change_management_default_days"] != 0.6


def test_put_effort_settings_rejects_invalid_percent(client):
    resp = client.put(
        "/settings/effort",
        json={
            "change_management_default_days": 0.5,
            "enhancement_coordination_percent": 1.5,  # >1, invalid
            "cost_bands": [{"label": "a", "upper_bound_days": 1, "cost_eur": 100}],
        },
    )
    assert resp.status_code == 422
