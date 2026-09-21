from hashlib import sha256

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from pydantic import BaseModel


MAX_FILE_SIZE_MIB = 10
MAX_FILE_SIZE = MAX_FILE_SIZE_MIB * 1024 * 1024

SUPPORTED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
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
    if file.content_type not in SUPPORTED_CONTENT_TYPES:
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

    return DocumentUploadResponse(
        filename=file.filename or "unknown",
        content_type=file.content_type,
        size=len(content),
        sha256=sha256(content).hexdigest(),
    )

