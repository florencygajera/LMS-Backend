"""
Summarization Router
POST /api/summarize
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

try:
    from agniassist.main import verify_token
except ModuleNotFoundError:
    from main import verify_token

router = APIRouter()


class SummarizeRequest(BaseModel):
    text: str
    max_length: Optional[int] = 150
    min_length: Optional[int] = 30


class SummarizeResponse(BaseModel):
    success: bool
    summary: str
    original_length: int
    summary_length: int
    compression_ratio: float
    method: str
    error: Optional[str] = None


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_text(
    request: SummarizeRequest,
    user: dict = Depends(verify_token)
):
    """Summarize text using Generative AI"""
    from agniassist.services.genai_service import genai_service
    
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    if len(request.text.split()) < 10:
        raise HTTPException(status_code=400, detail="Text too short for summarization")
    
    try:
        result = await genai_service.summarize(
            text=request.text,
            max_length=request.max_length,
            min_length=request.min_length
        )
        
        return SummarizeResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract_entities")
async def extract_entities(
    text: str,
    user: dict = Depends(verify_token)
):
    """Extract named entities from text"""
    from agniassist.services.nlp_service import nlp_service
    
    try:
        result = await nlp_service.extract_entities(text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze_sentiment")
async def analyze_text_sentiment(
    text: str,
    user: dict = Depends(verify_token)
):
    """Analyze sentiment of text"""
    from agniassist.services.nlp_service import nlp_service
    
    try:
        result = await nlp_service.analyze_sentiment(text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract_keywords")
async def extract_text_keywords(
    text: str,
    top_n: int = 10,
    user: dict = Depends(verify_token)
):
    """Extract keywords from text"""
    from agniassist.services.nlp_service import nlp_service
    
    try:
        keywords = await nlp_service.extract_keywords(text, top_n)
        return {
            "success": True,
            "keywords": keywords,
            "count": len(keywords)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
