from .conftest import RESUME_MEDIUM, RESUME_STRONG, RESUME_WEAK, register_and_login


def add(client, auth, job_id, text):
    r = client.post(f"/api/jobs/{job_id}/candidates/text", headers=auth, json={"text": text})
    assert r.status_code == 201, r.text
    return r.json()


def test_candidates_ranked_by_score(client, auth, job):
    for text in (RESUME_WEAK, RESUME_STRONG, RESUME_MEDIUM):
        add(client, auth, job["id"], text)
    r = client.get(f"/api/jobs/{job['id']}/candidates", headers=auth)
    assert r.status_code == 200
    rows = r.json()
    assert [c["name"] for c in rows] == ["Riley Strong", "Morgan Medium", "Lee Weak"]
    assert [c["rank"] for c in rows] == [1, 2, 3]
    scores = [c["score"] for c in rows]
    assert scores == sorted(scores, reverse=True)


def test_status_notes_and_filters(client, auth, job):
    strong = add(client, auth, job["id"], RESUME_STRONG)
    add(client, auth, job["id"], RESUME_WEAK)

    r = client.patch(
        f"/api/candidates/{strong['id']}",
        headers=auth,
        json={"status": "shortlisted", "notes": "Call Tuesday"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "shortlisted" and r.json()["notes"] == "Call Tuesday"

    rows = client.get(f"/api/jobs/{job['id']}/candidates?status=shortlisted", headers=auth).json()
    assert [c["id"] for c in rows] == [strong["id"]]
    assert rows[0]["rank"] == 1  # rank is computed before filtering

    rows = client.get(f"/api/jobs/{job['id']}/candidates?min_score=90", headers=auth).json()
    assert [c["name"] for c in rows] == ["Riley Strong"]

    assert (
        client.patch(f"/api/candidates/{strong['id']}", headers=auth, json={"status": "hired"}).status_code
        == 422
    )
    assert client.get(f"/api/jobs/{job['id']}", headers=auth).json()["shortlisted_count"] == 1


def test_candidate_detail_has_explainable_breakdown(client, auth, job):
    c = add(client, auth, job["id"], RESUME_STRONG)
    detail = client.get(f"/api/candidates/{c['id']}", headers=auth).json()
    assert {b["key"] for b in detail["breakdown"]} == {
        "licenses",
        "sales",
        "customer_service",
        "bilingual",
        "location",
    }
    assert all(b["evidence"] for b in detail["breakdown"])
    assert detail["resume_text"].startswith("Riley Strong")


def test_outreach_draft_is_generated_not_sent(client, auth, job):
    c = add(client, auth, job["id"], RESUME_STRONG)
    r = client.post(
        f"/api/candidates/{c['id']}/outreach", headers=auth, json={"recruiter_name": "Pat Recruiter"}
    )
    assert r.status_code == 200
    draft = r.json()["outreach_draft"]
    assert draft.startswith("Subject:")
    assert "Hi Riley" in draft and "Pat Recruiter" in draft


def test_other_users_cannot_see_candidates(client, auth, job):
    c = add(client, auth, job["id"], RESUME_STRONG)
    other = register_and_login(client, "someone-else")
    assert client.get(f"/api/candidates/{c['id']}", headers=other).status_code == 404
    assert client.get(f"/api/jobs/{job['id']}/candidates", headers=other).status_code == 404
    assert client.get("/api/jobs", headers=other).json() == []


def test_delete_candidate_and_job(client, auth, job):
    c = add(client, auth, job["id"], RESUME_STRONG)
    assert client.delete(f"/api/candidates/{c['id']}", headers=auth).status_code == 204
    assert client.get(f"/api/candidates/{c['id']}", headers=auth).status_code == 404
    assert client.delete(f"/api/jobs/{job['id']}", headers=auth).status_code == 204
    assert client.get("/api/jobs", headers=auth).json() == []
