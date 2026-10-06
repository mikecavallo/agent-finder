from .conftest import RESUME_MEDIUM, RESUME_STRONG, make_docx, make_pdf


def upload(client, auth, job_id, files):
    return client.post(f"/api/jobs/{job_id}/candidates/upload", headers=auth, files=files)


def test_upload_txt_pdf_docx(client, auth, job):
    files = [
        ("files", ("strong.txt", RESUME_STRONG.encode(), "text/plain")),
        ("files", ("strong.pdf", make_pdf(RESUME_STRONG), "application/pdf")),
        (
            "files",
            (
                "medium.docx",
                make_docx(RESUME_MEDIUM),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
        ),
    ]
    r = upload(client, auth, job["id"], files)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["errors"] == []
    assert [c["source_filename"] for c in body["created"]] == ["strong.txt", "strong.pdf", "medium.docx"]

    by_file = {c["source_filename"]: c for c in body["created"]}
    for name in ("strong.txt", "strong.pdf"):
        c = by_file[name]
        assert c["name"] == "Riley Strong"
        assert c["email"] == "riley.strong@example.com"
        assert set(c["licenses"]) == {"P&C", "Life & Health"}
        assert "Spanish" in c["languages"]
    assert by_file["strong.txt"]["score"] == by_file["strong.pdf"]["score"]
    assert by_file["medium.docx"]["name"] == "Morgan Medium"


def test_unsupported_and_empty_files_reported(client, auth, job):
    files = [
        ("files", ("resume.exe", b"MZ...", "application/octet-stream")),
        ("files", ("tiny.txt", b"too short", "text/plain")),
        ("files", ("good.txt", RESUME_STRONG.encode(), "text/plain")),
    ]
    r = upload(client, auth, job["id"], files)
    assert r.status_code == 201
    body = r.json()
    assert len(body["created"]) == 1
    assert {e["filename"] for e in body["errors"]} == {"resume.exe", "tiny.txt"}


def test_all_files_invalid_is_422(client, auth, job):
    r = upload(client, auth, job["id"], [("files", ("bad.pdf", b"not a pdf", "application/pdf"))])
    assert r.status_code == 422


def test_paste_text(client, auth, job):
    r = client.post(f"/api/jobs/{job['id']}/candidates/text", headers=auth, json={"text": RESUME_MEDIUM})
    assert r.status_code == 201, r.text
    assert r.json()["name"] == "Morgan Medium"
    assert r.json()["source_filename"] == "Pasted text"


def test_cannot_upload_to_another_users_job(client, auth, job):
    from .conftest import register_and_login

    other = register_and_login(client, "intruder")
    r = client.post(f"/api/jobs/{job['id']}/candidates/text", headers=other, json={"text": RESUME_MEDIUM})
    assert r.status_code == 404
