"""Validation for uploaded resume files and pasted text."""

import os

from fastapi import HTTPException, status

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MIN_RESUME_CHARS = 80
MAX_RESUME_CHARS = 60_000


def validate_filename(filename: str | None) -> str:
    if not filename:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File has no name.")
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"{filename}: unsupported file type. Upload PDF, DOCX or TXT.",
        )
    return ext


def validate_size(filename: str, size: int, max_mb: int) -> None:
    if size > max_mb * 1024 * 1024:
        raise HTTPException(413, f"{filename}: larger than {max_mb} MB.")
    if size == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{filename}: file is empty.")


def validate_resume_text(text: str, label: str = "Resume") -> str:
    cleaned = text.strip()
    if len(cleaned) < MIN_RESUME_CHARS:
        raise HTTPException(
            422,
            f"{label}: not enough text to screen (scanned PDFs without a text layer are not supported).",
        )
    return cleaned[:MAX_RESUME_CHARS]
