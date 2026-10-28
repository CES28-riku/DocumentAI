import sqlite3
from contextlib import closing
from enum import StrEnum
from pathlib import Path


CREATE_AMAZON_DOCUMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS amazon_documents (
    id INTEGER PRIMARY KEY,
    order_number TEXT NOT NULL,
    invoice_number TEXT NOT NULL,
    document_type TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (order_number, invoice_number)
)
"""


class RegistrationResult(StrEnum):
    """Possible outcomes when registering an Amazon document."""

    CREATED = "created"
    DUPLICATE = "duplicate"
    CONTENT_CHANGED = "content_changed"


def initialize_database(database_path: Path) -> None:
    """Create the database directory and the Amazon document table."""
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute(CREATE_AMAZON_DOCUMENTS_TABLE)
        connection.commit()


def register_document(
    database_path: Path,
    *,
    order_number: str,
    invoice_number: str,
    document_type: str,
    file_hash: str,
    storage_path: Path,
) -> RegistrationResult:
    """Register a document and describe how it compares with an existing row."""
    with closing(sqlite3.connect(database_path)) as connection:
        cursor = connection.execute(
            """
            INSERT INTO amazon_documents (
                order_number,
                invoice_number,
                document_type,
                file_hash,
                storage_path
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (order_number, invoice_number) DO NOTHING
            """,
            (
                order_number,
                invoice_number,
                document_type,
                file_hash,
                str(storage_path),
            ),
        )
        connection.commit()

        if cursor.rowcount == 1:
            return RegistrationResult.CREATED

        existing_row = connection.execute(
            """
            SELECT file_hash
            FROM amazon_documents
            WHERE order_number = ? AND invoice_number = ?
            """,
            (order_number, invoice_number),
        ).fetchone()

        if existing_row is None:
            raise RuntimeError("The conflicting document could not be found.")

        existing_file_hash = existing_row[0]

        if existing_file_hash == file_hash:
            return RegistrationResult.DUPLICATE

        return RegistrationResult.CONTENT_CHANGED
