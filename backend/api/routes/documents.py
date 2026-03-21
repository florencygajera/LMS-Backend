"""
Document service API endpoints.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from core.authorization import admin_required
from models.user import User
from services.ocr_service import ocr_service


router = APIRouter()

@router.get("/")
async def document_service_test():
    return {"message": "document service working"}


@router.get("/health")
async def document_health():
    return {"status": "healthy", "service": "documents"}


@router.post("/ocr")
async def process_document_ocr(
    document_type: str,
    file: UploadFile = File(...),
    current_user: User = Depends(admin_required),
):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is required")

    result = await ocr_service.process_document(document_type, await file.read())
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=result.get("error", "OCR Failed"))
        
    extracted_text = result.get("extracted_text", "")
    if extracted_text:
        # Dynamically map the portal's newly OCR'd document directly into the AI's permanent semantic memory pool
        from agniassist.services.rag_service import rag_service
        doc_metadata = f"[PORTAL_UPLOAD] Document Type: {document_type.upper()}. Extracted Text: {extracted_text}"
        try:
            rag_service.integrate_document(doc_metadata)
        except Exception:
            pass # Failsafe incase index process is locked
            
    return result





