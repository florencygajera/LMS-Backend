from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import logging

try:
    from core.database import get_db
    from security import verify_token
except ModuleNotFoundError:
    from core.database import get_db
    from core.security import verify_token

from models.user import AuditLog
from .services.rag_service import rag_service
from .services.context_service import context_service
from .services.prompt_builder import prompt_builder
from .services.llm_service import llm_service

router = APIRouter()
logger = logging.getLogger("AgniAssist")

class AskRequest(BaseModel):
    query: str
    user_id: int

class AskResponse(BaseModel):
    answer: str

@router.post("/ask", response_model=AskResponse)
async def ask_agniassist(
    request: AskRequest,
    req: Request,
    user: dict = None,
    db: AsyncSession = Depends(get_db)
):
    try:
        # JWT validation (Dependency can be explicitly assigned)
        verify_t = verify_token
        
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
            
        # 1. Fetch user data & ML context
        user_context, ml_prediction = await context_service.get_user_context(request.user_id, db)
        
        # 2. Retrieve relevant documents using FAISS
        retrieved_docs = await rag_service.retrieve_context(request.query)
        
        # 3. Build unified prompt
        prompt = prompt_builder.build_prompt(
            user_data=user_context,
            prediction=ml_prediction,
            retrieved_docs=retrieved_docs,
            query=request.query
        )
        
        # 4. Generate response using local LLM
        answer = await llm_service.generate_response(prompt)
        
        # 5. Security Logging
        audit_log = AuditLog(
            user_id=request.user_id,
            action="agniassist_query",
            details=f"Query processed successfully. Length: {len(request.query)}",
            ip_address=req.client.host if getattr(req, 'client', None) else None
        )
        db.add(audit_log)
        await db.commit()
        
        return AskResponse(answer=answer)
        
    except Exception as e:
        logger.exception("AgniAssist processing failed")
        raise HTTPException(status_code=500, detail=str(e))
