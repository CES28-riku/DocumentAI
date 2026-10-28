import sqlite3
from contextlib import closing
from pathlib import Path

from app.database import RegistrationResult, initialize_database, register_document


def count_documents(database_path: Path) -> int:
    """Return the number of rows so tests can verify the persisted result."""
    with closing(sqlite3.connect(database_path)) as connection:
        result = connection.execute(
            "SELECT COUNT(*) FROM amazon_documents"
        ).fetchone()

    assert result is not None
    return result[0]


def get_file_hash(database_path: Path) -> str:
    """Return the stored hash so tests can verify it was not overwritten."""
    with closing(sqlite3.connect(database_path)) as connection:
        result = connection.execute(
            "SELECT file_hash FROM amazon_documents"
        ).fetchone()

    assert result is not None
    return result[0]


def test_registering_same_order_and_invoice_twice_creates_one_row(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "documents.db"
    initialize_database(database_path)

    first_result = register_document(
        database_path,
        order_number="order-001",
        invoice_number="invoice-001",
        document_type="qualified_invoice",
        file_hash="hash-001",
        storage_path=Path("storage/raw/hash-001.pdf"),
    )
    second_result = register_document(
        database_path,
        order_number="order-001",
        invoice_number="invoice-001",
        document_type="qualified_invoice",
        file_hash="hash-001",
        storage_path=Path("storage/raw/hash-001.pdf"),
    )

    assert first_result == RegistrationResult.CREATED
    assert second_result == RegistrationResult.DUPLICATE
    assert count_documents(database_path) == 1


def test_same_order_with_different_invoices_creates_two_rows(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "documents.db"
    initialize_database(database_path)

    first_result = register_document(
        database_path,
        order_number="order-001",
        invoice_number="invoice-001",
        document_type="qualified_invoice",
        file_hash="hash-001",
        storage_path=Path("storage/raw/hash-001.pdf"),
    )
    second_result = register_document(
        database_path,
        order_number="order-001",
        invoice_number="invoice-002",
        document_type="qualified_invoice",
        file_hash="hash-002",
        storage_path=Path("storage/raw/hash-002.pdf"),
    )

    assert first_result == RegistrationResult.CREATED
    assert second_result == RegistrationResult.CREATED
    assert count_documents(database_path) == 2


def test_same_business_key_with_different_hash_reports_content_change(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "documents.db"
    initialize_database(database_path)

    first_result = register_document(
        database_path,
        order_number="order-001",
        invoice_number="invoice-001",
        document_type="qualified_invoice",
        file_hash="original-hash",
        storage_path=Path("storage/raw/original-hash.pdf"),
    )
    second_result = register_document(
        database_path,
        order_number="order-001",
        invoice_number="invoice-001",
        document_type="qualified_invoice",
        file_hash="changed-hash",
        storage_path=Path("storage/raw/changed-hash.pdf"),
    )

    assert first_result == RegistrationResult.CREATED
    assert second_result == RegistrationResult.CONTENT_CHANGED
    assert count_documents(database_path) == 1
    assert get_file_hash(database_path) == "original-hash"
