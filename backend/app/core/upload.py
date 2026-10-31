"""Secure file upload validator enforcing MIME type and size policies (NFR 4.2)."""

import os
import uuid
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from app.config import settings

# Allowed image magic byte headers
MAGIC_BYTES = {
    "jpg": b"\xff\xd8\xff",
    "jpeg": b"\xff\xd8\xff",
    "png": b"\x89PNG\r\n\x1a\n"
}

def validate_and_save_photo(file: Optional[UploadFile]) -> Optional[str]:
    """
    Validate uploaded photo according to NFR 4.2:
    - Maximum 5 MB in size
    - Checked by actual file type (magic bytes), not trusted by filename
    - Limited to JPG and PNG
    Returns relative URL path to saved file (e.g. '/uploads/uuid.png'), or None if no file.
    """
    if file is None or not file.filename:
        return None

    # Read the first chunk to inspect magic bytes and calculate size
    header = file.file.read(8)
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    # 1. Enforce 5 MB maximum size constraint (F4, NFR 4.2)
    if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Photo size ({file_size / (1024 * 1024):.2f} MB) exceeds maximum allowed limit of 5 MB."
        )

    # 2. Enforce file type by inspecting actual binary magic bytes (NFR 4.2)
    detected_extension = None
    if header.startswith(MAGIC_BYTES["png"]):
        detected_extension = "png"
    elif header.startswith(b"\xff\xd8\xff"):
        detected_extension = "jpg"

    if not detected_extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file type. Only genuine JPG and PNG photos are accepted (verified by file content, not name)."
        )

    # 3. Save with secure UUID filename
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{detected_extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        content = file.file.read()
        buffer.write(content)

    return f"/uploads/{filename}"
