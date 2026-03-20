"""
RAG Chatbot Router
POST /api/ask
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

try:
    from agniassist.security import verify_token
except ModuleNotFoundError:
    from security import verify_token

router = APIRouter()


class AskRequest(BaseModel):
    query: str
    top_k: Optional[int] = 3


class AskResponse(BaseModel):
    answer: str
    sources: list
    context_used: bool


@router.post("/ask", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    user: dict = Depends(verify_token)
):
    """Ask a question to the RAG chatbot"""
    from agniassist.services.rag_service import rag_service
    
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        result = await rag_service.query(
            query_text=request.query,
            top_k=request.top_k
        )
        
        return AskResponse(
            answer=result.get("answer", "No answer generated"),
            sources=result.get("sources", []),
            context_used=result.get("context_used", False)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/add_document")
async def add_document(
    title: str,
    content: str,
    category: str = "general",
    user: dict = Depends(verify_token)
):
    """Add a document to the knowledge base"""
    from agniassist.services.rag_service import rag_service
    
    try:
        await rag_service.add_document(title, content, category)
        return {"success": True, "message": f"Document '{title}' added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




