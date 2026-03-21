import os
import sys
import asyncio
from sqlalchemy import select

# Must add backend to path to import correctly
sys.path.insert(0, os.path.dirname(__file__) + r"\..\..")

from core.database import get_async_session_local, import_models
from agniassist.services.rag_service import rag_service

# Import the actual portal tables
from models.user import User
from models.soldier import Battalion, Soldier, TrainingRecord, MedicalRecord
from models.recruitment import ExamCenter, Exam, Candidate

async def sync_database_knowledge():
    """Extracts raw production database rows and maps them into FAISS semantic memory."""
    import_models()
    session_factory = get_async_session_local()
    
    count = 0
    print("🔄 Initializing dynamic Database-to-FAISS synchronization...")
    
    async with session_factory() as db:
        
        # 1. Sync Battalion Data
        battalions = await db.execute(select(Battalion))
        for b in battalions.scalars():
            doc = f"[BATTALION] Battalion {b.battalion_name} ({b.battalion_code}) is located in {b.city}, {b.state}. Commanded by {b.commander_name}. Mission: {b.mission_details}. Total Strength: {b.total_strength}."
            rag_service.integrate_document(doc)
            count += 1
            
        # 2. Sync Exam Centers
        centers = await db.execute(select(ExamCenter))
        for c in centers.scalars():
            doc = f"[EXAM_CENTER] Center {c.center_name} ({c.center_code}) is located at {c.address}, {c.city}. Capacity is {c.capacity} with {c.current_booked} booked."
            rag_service.integrate_document(doc)
            count += 1
            
        # 3. Sync Exams
        exams = await db.execute(select(Exam))
        for e in exams.scalars():
            doc = f"[EXAM] {e.exam_name} ({e.exam_code}) scheduled for {e.exam_date}. Duration: {e.duration_minutes} minutes. Pass marks: {e.passing_marks} out of {e.total_marks}."
            rag_service.integrate_document(doc)
            count += 1
            
        # 4. Sync Global Platform Stats (Contextual Meta-information)
        users = (await db.execute(select(User))).scalars().all()
        soldiers = (await db.execute(select(Soldier))).scalars().all()
        candidates = (await db.execute(select(Candidate))).scalars().all()
        
        system_doc = f"[SYSTEM_STATS] The portal currently has {len(users)} registered users, comprising {len(candidates)} enrollment candidates and {len(soldiers)} active duty soldiers."
        rag_service.integrate_document(system_doc)
        count += 1
        
        # 5. Sync Soldier Knowledge/Metrics
        trainings = await db.execute(select(TrainingRecord).limit(100)) # Sample latest
        for t in trainings.scalars().all():
            doc = f"[TRAINING_METRIC] Soldier ID {t.soldier_id} on {t.training_date} completed {t.training_type} training. Score: {t.overall_score}. Pushups: {t.pushups_count}, Pullups: {t.pullups_count}."
            rag_service.integrate_document(doc)
            count += 1

    print(f"✅ Extracted and Indexed {count} distinct platform database parameters into AI Memory!")
    print(f"Total Institutional Knowledge Base items: {rag_service.index.ntotal}")

if __name__ == "__main__":
    asyncio.run(sync_database_knowledge())
