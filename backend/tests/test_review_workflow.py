from datetime import datetime

from app.db import AnalysisRun, get_session

SAMPLE_RESULT = {
    "requirement": {
        "objective": "x",
        "scope": "y",
        "constraints": [],
        "acceptance_criteria": [],
        "affected_application": "SanofiOrders",
    },
    "impacted_items": [],
    "dependencies": [],
    "risks": [],
    "effort_estimate": {
        "analysis_design_days": 0.1,
        "build_days": 1.0,
        "testing_sit_days": 0.5,
        "uat_support_days": 0.25,
        "change_management_days": 0.5,
        "enhancement_coordination_days": 0.185,
        "total_days": 2.535,
        "complexity": "Medium",
        "confidence": 0.7,
        "rationale": "test",
        "cost_status": "Computed",
        "cost_eur": 505.0,
        "cost_band_label": "2-5 days",
    },
    "test_scenarios": [],
    "needs_validation": [],
}


def _create_cr(client):
    resp = client.post(
        "/change-requests",
        json={"application": "SanofiOrders", "summary": "Test CR", "description": "desc", "priority": "Medium"},
    )
    assert resp.status_code == 200
    return resp.json()["id"]


def _insert_completed_run(cr_id: int, review_status: str = "NotReviewed") -> int:
    session = get_session()
    try:
        run = AnalysisRun(
            change_request_id=cr_id,
            model="gpt-4o-mini",
            status="Completed",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            result=SAMPLE_RESULT,
            review_status=review_status,
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        return run.id
    finally:
        session.close()


def test_accept_locks_run_and_marks_cr_approved(client):
    cr_id = _create_cr(client)
    run_id = _insert_completed_run(cr_id)

    resp = client.post(f"/analysis-runs/{run_id}/feedback", json={"user": "tl@x.com", "decision": "Accepted"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["review_status"] == "Approved"
    assert body["decided_by"] == "tl@x.com"

    cr = client.get(f"/change-requests/{cr_id}").json()
    assert cr["status"] == "Approved"


def test_double_decision_is_rejected_with_409(client):
    cr_id = _create_cr(client)
    run_id = _insert_completed_run(cr_id)

    first = client.post(f"/analysis-runs/{run_id}/feedback", json={"user": "tl@x.com", "decision": "Accepted"})
    assert first.status_code == 200

    second = client.post(f"/analysis-runs/{run_id}/feedback", json={"user": "tl@x.com", "decision": "Rejected"})
    assert second.status_code == 409


def test_reject_marks_cr_rejected(client):
    cr_id = _create_cr(client)
    run_id = _insert_completed_run(cr_id)

    resp = client.post(f"/analysis-runs/{run_id}/feedback", json={"user": "tl@x.com", "decision": "Rejected"})
    assert resp.status_code == 200
    assert resp.json()["review_status"] == "Rejected"

    cr = client.get(f"/change-requests/{cr_id}").json()
    assert cr["status"] == "Rejected"


def test_edited_decision_requires_edited_result(client):
    cr_id = _create_cr(client)
    run_id = _insert_completed_run(cr_id)

    resp = client.post(f"/analysis-runs/{run_id}/feedback", json={"user": "tl@x.com", "decision": "Edited"})
    assert resp.status_code == 422


def test_edited_decision_preserves_original_and_saves_edit(client):
    cr_id = _create_cr(client)
    run_id = _insert_completed_run(cr_id)

    edited = dict(SAMPLE_RESULT)
    edited["requirement"] = {**SAMPLE_RESULT["requirement"], "objective": "edited objective"}

    resp = client.post(
        f"/analysis-runs/{run_id}/feedback",
        json={"user": "tl@x.com", "decision": "Edited", "comment": "bumped estimate", "edited_result": edited},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["review_status"] == "ApprovedEdited"
    assert body["result"]["requirement"]["objective"] == "edited objective"
    assert body["ai_original_result"]["requirement"]["objective"] == "x"


def test_reestimate_effort_blocked_on_reviewed_run(client):
    cr_id = _create_cr(client)
    run_id = _insert_completed_run(cr_id, review_status="Approved")

    resp = client.post(
        f"/analysis-runs/{run_id}/re-estimate-effort",
        json={"requirement": SAMPLE_RESULT["requirement"], "impacted_items": []},
    )
    assert resp.status_code == 409


def test_feedback_on_missing_run_is_404(client):
    resp = client.post("/analysis-runs/999999/feedback", json={"user": "tl@x.com", "decision": "Accepted"})
    assert resp.status_code == 404
