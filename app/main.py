from hashlib import sha256
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from pydantic import BaseModel


MAX_FILE_SIZE_MIB = 10
MAX_FILE_SIZE = MAX_FILE_SIZE_MIB * 1024 * 1024

FILE_SIGNATURES = {
    "application/pdf": (b"%PDF-",),
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
}

STORAGE_DIR = Path("storage/raw")

CONTENT_TYPE_EXTENSIONS = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}

app = FastAPI(title="Document AI API")


class DocumentUploadResponse(BaseModel):
    filename: str
    content_type: str
    size: int
    sha256: str


@app.post(
    "/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    if file.content_type not in FILE_SIGNATURES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF, JPEG, and PNG files are supported.",
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"The uploaded file exceeds the {MAX_FILE_SIZE_MIB} MiB limit.",
        )

    expected_signatures = FILE_SIGNATURES[file.content_type]

    if not content.startswith(expected_signatures):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="The file content does not match its declared content type.",
        )

    return DocumentUploadResponse(
        filename=file.filename or "unknown",
        content_type=file.content_type,
        size=len(content),
        sha256=sha256(content).hexdigest(),
    )

def build_storage_path(file_hash: str, content_type: str) -> Path:
    extension = CONTENT_TYPE_EXTENSIONS[content_type]
    return STORAGE_DIR / f"{file_hash}{extension}"