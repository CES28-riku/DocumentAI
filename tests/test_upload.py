from hashlib import sha256
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import (
    MAX_FILE_SIZE,
    MAX_FILE_SIZE_MIB,
    app,
    build_storage_path,
)


client = TestClient(app)


def test_upload_pdf_returns_file_metadata() -> None:
    content = b"%PDF-1.4 sample invoice"

    response = client.post(
        "/documents",
        files={"file": ("invoice.pdf", content, "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json() == {
        "filename": "invoice.pdf",
        "content_type": "application/pdf",
        "size": len(content),
        "sha256": sha256(content).hexdigest(),
    }


def test_upload_rejects_unsupported_content_type() -> None:
    response = client.post(
        "/documents",
        files={"file": ("invoice.txt", b"invoice", "text/plain")},
    )

    assert response.status_code == 415


def test_upload_rejects_empty_file() -> None:
    response = client.post(
        "/documents",
        files={"file": ("invoice.pdf", b"", "application/pdf")},
    )

    assert response.status_code == 400


def test_upload_rejects_file_larger_than_limit() -> None:
    content = b"x" * (MAX_FILE_SIZE + 1)

    response = client.post(
        "/documents",
        files={"file": ("invoice.pdf", content, "application/pdf")},
    )

    assert response.status_code == 413
    assert response.json() == {
        "detail": f"The uploaded file exceeds the {MAX_FILE_SIZE_MIB} MiB limit."
    }


def test_upload_rejects_content_that_does_not_match_declared_type() -> None:
    response = client.post(
        "/documents",
        files={
            "file": (
                "fake.pdf",
                b"this is not a PDF",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 415
    assert response.json() == {
        "detail": "The file content does not match its declared content type."
    }


def test_build_storage_path_uses_hash_and_content_type_extension() -> None:
    result = build_storage_path("abc123", "application/pdf")

    assert result == Path("storage/raw/abc123.pdf")
