"""
OCR Router
POST /api/ocr
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional

try:
    from agniassist.main import verify_token
except ModuleNotFoundError:
    from main import verify_token

router = APIRouter()


class OCRResponse(BaseModel):
    success: bool
    text: str
    confidence: float
    fields: dict
    raw_text: Optional[str] = None
    error: Optional[str] = None


@router.post("/ocr", response_model=OCRResponse)
async def process_ocr(
    file: UploadFile = File(...),
    user: dict = Depends(verify_token)
):
    """Process image and extract text using OCR"""
    from agniassist.services.ocr_service import ocr_service
    
    # Validate file type
    allowed_types = {"image/png", "image/jpeg", "image/jpg", "image/tiff", "image/bmp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {allowed_types}"
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Check file size (max 10MB)
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
        # Process
        result = await ocr_service.process_image(content)
        
        return OCRResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ocr/extract_entities")
async def extract_entities(
    text: str,
    user: dict = Depends(verify_token)
):
    """Extract entities from OCR text"""
    from agniassist.services.nlp_service import nlp_service
    
    try:
        result = await nlp_service.extract_entities(text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
