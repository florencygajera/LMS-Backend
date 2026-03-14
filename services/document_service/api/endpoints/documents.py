"""
Document service API endpoints.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from common.core.authorization import admin_required
from services.auth_service.models.user import User
from services.document_service.services.ocr_service import ocr_service


router = APIRouter()


@router.post("/ocr")
async def process_document_ocr(
    document_type: str,
    file: UploadFile = File(...),
    current_user: User = Depends(admin_required),
):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is required")

    result = await ocr_service.process_document(document_type, await file.read())
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=result["error"])
    return result
