"""
OCR Background Tasks
Agniveer Sentinel - Enterprise Production
"""

from core.celery_config import celery_app, BaseTask
from celery import chain, group
import asyncio

from core.storage import storage


@celery_app.task(base=BaseTask, bind=True, max_retries=3)
def process_ocr_document(self, document_id: int, document_type: str):
    """Process OCR for uploaded document"""
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from models.recruitment import CandidateDocument
    from models.soldier import SoldierDocument
    from services.document_service.services.ocr_service import ocr_service
    
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    
    async def _process():
        # Get database URL
        db_url = os.getenv(
            "DATABASE_URL", 
            "postgresql+asyncpg://postgres:postgres@localhost:5432/agniveer_db"
        )
        
        engine = create_async_engine(db_url)
        async with AsyncSession(engine) as session:
            # Determine which model to query based on document type
            if document_type == "candidate":
                result = await session.execute(
                    select(CandidateDocument).where(CandidateDocument.id == document_id)
                )
            else:
                result = await session.execute(
                    select(SoldierDocument).where(SoldierDocument.id == document_id)
                )
            
            document = result.scalar_one_or_none()
            
            if not document:
                return {"error": "Document not found"}
            
            file_content = storage.download_bytes(document.file_url)
            
            # Process OCR
            result = await ocr_service.process_document(document.document_type, file_content)
            
            if result["success"]:
                document.ocr_processed = True
                document.ocr_text = result["text"]
                parsed_data = result.get("parsed_data") or {}

                if document_type != "candidate" and parsed_data:
                    result = await session.execute(
                        select(SoldierDocument).where(SoldierDocument.id == document_id)
                    )
                    soldier_document = result.scalar_one_or_none()
                    if soldier_document:
                        from models.soldier import Soldier

                        soldier_result = await session.execute(
                            select(Soldier).where(Soldier.id == soldier_document.soldier_id)
                        )
                        soldier = soldier_result.scalar_one_or_none()
                        if soldier:
                            if parsed_data.get("name") and not soldier.full_name:
                                soldier.full_name = parsed_data["name"]
                            if parsed_data.get("address") and not soldier.permanent_address:
                                soldier.permanent_address = parsed_data["address"]
                            if parsed_data.get("gender") and not soldier.gender:
                                soldier.gender = parsed_data["gender"]
                await session.commit()
            
            return result
    
    # Run async function
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_process())


@celery_app.task(base=BaseTask, bind=True)
def process_batch_ocr(self, document_ids: list, document_type: str):
    """Process multiple OCR documents in parallel"""
    # Create a group of tasks for parallel processing
    tasks = group(
        process_ocr_document.s(doc_id, document_type)
        for doc_id in document_ids
    )
    
    result = tasks.apply_async()
    return {"batch_id": result.id, "total": len(document_ids)}


@celery_app.task(base=BaseTask, bind=True, max_retries=2)
def extract_profile_data(self, document_id: int, soldier_id: int = None):
    """Extract and update profile data from OCR"""
    
    async def _extract():
        return process_ocr_document(document_id, "soldier")
    
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_extract())





