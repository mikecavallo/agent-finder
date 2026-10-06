import os
import sys
import tempfile
from pathlib import Path

# Configure the app before it is imported: isolated SQLite file, offline mock scorer.
_tmpdir = tempfile.mkdtemp(prefix="agent-finder-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmpdir}/test.db"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-hs256"
os.environ["DEMO_MODE"] = "false"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.ai.providers import set_provider_override  # noqa: E402
from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

RESUME_STRONG = """Riley Strong
Wilmington, NC | riley.strong@example.com | 910-555-0110

Licensed agent with five years of sales experience. Bilingual English and Spanish.
Licenses: NC Property & Casualty, NC Life & Health
Insurance Sales Agent | Example Agency | Wilmington, NC | 2019 - 2024
Customer Service Representative | Example Bank | Wilmington, NC | 2016 - 2019
Languages: English, Spanish
"""

RESUME_MEDIUM = """Morgan Medium
Raleigh, NC | morgan.medium@example.com | 919-555-0111

Retail sales associate looking to move into insurance. Friendly and reliable.
Retail Sales Associate | Example Store | Raleigh, NC | 2021 - 2024
Customer Service Representative | Example Call Center | Raleigh, NC | 2019 - 2021
"""

RESUME_WEAK = """Lee Weak
Denver, CO | lee.weak@example.com | 303-555-0112

Warehouse associate with a strong safety record and excellent attendance history.
Warehouse Associate | Example Logistics | Denver, CO | 2018 - 2024
"""


@pytest.fixture(autouse=True)
def fresh_db():
    from app import models  # noqa: F401

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    set_provider_override(None)
    yield
    set_provider_override(None)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def register_and_login(client, username="recruiter", password="correct-horse-1"):
    r = client.post(
        "/api/auth/register",
        json={"username": username, "email": f"{username}@example.com", "password": password},
    )
    assert r.status_code == 201, r.text
    r = client.post("/api/auth/token", data={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def auth(client):
    return register_and_login(client)


@pytest.fixture
def job(client, auth):
    r = client.post(
        "/api/jobs",
        headers=auth,
        json={
            "title": "Insurance Agent",
            "location": "Wilmington, NC",
            "criteria": {
                "required_licenses": ["P&C", "Life & Health"],
                "min_sales_years": 2,
                "customer_service_required": True,
                "bilingual_preferred": True,
                "languages": ["Spanish"],
            },
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def make_pdf(text: str) -> bytes:
    """Build a minimal single-page PDF with a real text layer (no extra dependencies)."""
    lines = text.splitlines()
    ops = ["BT", "/F1 11 Tf", "14 TL", "50 750 Td"]
    for line in lines:
        safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        ops.append(f"({safe}) Tj T*")
    ops.append("ET")
    stream = "\n".join(ops).encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


def make_docx(text: str) -> bytes:
    import io

    from docx import Document

    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
