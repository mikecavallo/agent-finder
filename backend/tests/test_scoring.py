import asyncio
from datetime import date

from app.ai.extraction import extract_profile
from app.ai.providers import JobContext, MockProvider
from app.ai.rubric import JobCriteria, aggregate

from .conftest import RESUME_MEDIUM, RESUME_STRONG, RESUME_WEAK


def test_extraction_fields():
    p = extract_profile(RESUME_STRONG, today=date(2025, 1, 1)).profile
    assert p.name == "Riley Strong"
    assert p.phone == "910-555-0110"
    assert p.location == "Wilmington, NC"
    assert p.licenses == ["P&C", "Life & Health"]
    assert p.years_sales == 5
    assert p.years_customer_service == 3
    assert p.current_title == "Insurance Sales Agent"


def test_license_in_progress_is_not_held():
    text = (
        "Pat Example\nRaleigh, NC\nCurrently studying for the Property & Casualty license exam.\n" + "x" * 80
    )
    assert extract_profile(text).profile.licenses == []


def test_aggregate_uses_weights():
    total, breakdown = aggregate(
        {
            "licenses": (1.0, ""),
            "sales": (0.5, ""),
            "customer_service": (0.0, ""),
            "bilingual": (1.0, ""),
            "location": (1.0, ""),
        },
        {"licenses": 30, "sales": 20, "customer_service": 20, "bilingual": 0, "location": 30},
    )
    assert total == 70.0  # (30 + 10 + 0 + 30) / 100
    assert [b.key for b in breakdown] == ["licenses", "sales", "customer_service", "bilingual", "location"]
    assert breakdown[3].evidence == "Not weighted for this opening."


def test_scores_are_clamped():
    total, _ = aggregate({"licenses": (5.0, "")}, {"licenses": 10})
    assert total == 100.0


def test_unused_criteria_get_zero_weight():
    c = JobCriteria(bilingual_preferred=False, customer_service_required=False)
    w = c.effective_weights(location="")
    assert w["bilingual"] == 0 and w["customer_service"] == 0 and w["location"] == 0


def test_mock_scores_are_deterministic_and_ordered():
    ctx = JobContext(
        title="Agent",
        location="Wilmington, NC",
        description="",
        criteria=JobCriteria(
            required_licenses=["P&C", "Life & Health"], bilingual_preferred=True, languages=["Spanish"]
        ),
    )
    provider = MockProvider(today=date(2025, 1, 1))
    weights = ctx.criteria.effective_weights(ctx.location)

    def score(text):
        result = asyncio.run(provider.screen(text, ctx))
        return aggregate(result.assessments, weights)[0]

    strong, medium, weak = score(RESUME_STRONG), score(RESUME_MEDIUM), score(RESUME_WEAK)
    assert strong == score(RESUME_STRONG)
    assert strong == 100.0
    assert strong > medium > weak


def test_rescore_after_criteria_change(client, auth, job):
    r = client.post(f"/api/jobs/{job['id']}/candidates/text", headers=auth, json={"text": RESUME_MEDIUM})
    cid = r.json()["id"]
    before = r.json()["score"]
    # Drop the license requirement entirely: Morgan Medium has no licenses, so the score should rise.
    criteria = dict(
        job["criteria"],
        required_licenses=[],
        weights={"licenses": 0, "sales": 25, "customer_service": 20, "bilingual": 10, "location": 15},
    )
    assert (
        client.patch(f"/api/jobs/{job['id']}", headers=auth, json={"criteria": criteria}).status_code == 200
    )
    after = client.post(f"/api/candidates/{cid}/rescore", headers=auth).json()
    assert after["score"] > before
    assert after["breakdown"][0]["weight"] == 0
