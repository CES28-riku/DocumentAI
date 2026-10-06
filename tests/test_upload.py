from hashlib import sha256
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import (
    MAX_FILE_SIZE,
    MAX_FILE_SIZE_MIB,
    app,
    build_storage_path,
    save_document,
)

from pytest import MonkeyPatch


client = TestClient(app)


def test_upload_pdf_returns_file_metadata(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.main.STORAGE_DIR", tmp_path)

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
        "stored": True,
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


def test_save_document_does_not_overwrite_existing_file(tmp_path: Path) -> None:
    storage_path = tmp_path / "raw" / "abc123.pdf"
    original_content = b"%PDF-1.4 original"
    different_content = b"%PDF-1.4 different"

    first_result = save_document(original_content, storage_path)
    second_result = save_document(different_content, storage_path)

    assert first_result is True
    assert second_result is False
    assert storage_path.read_bytes() == original_content


def test_uploading_same_pdf_twice_does_not_create_duplicate(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.main.STORAGE_DIR", tmp_path)

    content = b"%PDF-1.4 duplicate test"
    files = {
        "file": ("invoice.pdf", content, "application/pdf"),
    }

    first_response = client.post("/documents", files=files)
    second_response = client.post("/documents", files=files)

    file_hash = sha256(content).hexdigest()
    saved_path = tmp_path / f"{file_hash}.pdf"

    assert first_response.json()["stored"] is True
    assert second_response.json()["stored"] is False
    assert saved_path.read_bytes() == content
    assert len(list(tmp_path.iterdir())) == 1