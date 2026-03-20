"""
Report Background Tasks
Agniveer Sentinel - Enterprise Production
"""

from infrastructure.celery_config import celery_app, BaseTask
from celery import group
from datetime import datetime, date
import asyncio


@celery_app.task(base=BaseTask, bind=True, max_retries=3)
def generate_daily_report(self, soldier_id: int, report_date: date = None):
    """Generate daily performance report for a soldier"""
    
    async def _generate():
        import os
        db_url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/agniveer_db"
        )
        
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy import select
        from models.soldier import Soldier, TrainingRecord
        from services.report_generator import pdf_generator
        
        engine = create_async_engine(db_url)
        
        async with AsyncSession(engine) as session:
            # Get soldier
            result = await session.execute(select(Soldier).where(Soldier.id == soldier_id))
            soldier = result.scalar_one_or_none()
            
            if not soldier:
                return {"error": "Soldier not found"}
            
            # Get training records
            target_date = report_date or date.today()
            result = await session.execute(
                select(TrainingRecord).where(
                    TrainingRecord.soldier_id == soldier_id,
                    TrainingRecord.training_date == target_date
                )
            )
            records = result.scalars().all()
            
            # Prepare training data
            training_data = {}
            for record in records:
                if record.training_type.value == "fitness":
                    training_data["fitness"] = {
                        "running_time": record.running_time_minutes,
                        "pushups": record.pushups_count,
                        "endurance_score": record.endurance_score
                    }
                elif record.training_type.value == "weapons":
                    training_data["weapons"] = {
                        "shooting_accuracy": record.shooting_accuracy,
                        "weapon_handling": record.weapon_handling_score
                    }
                
                if record.overall_score:
                    training_data["overall_score"] = record.overall_score
                if record.remarks:
                    training_data["remarks"] = record.remarks
            
            # Generate PDF
            pdf_content = pdf_generator.generate_daily_performance_report(
                soldier_name=soldier.full_name,
                soldier_id=soldier.soldier_id,
                training_date=target_date,
                training_data=training_data
            )
            
            # Upload to storage
            # In production, would upload to S3
            
            return {
                "status": "success",
                "soldier_id": soldier_id,
                "date": str(target_date),
                "pdf_size": len(pdf_content)
            }
    
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_generate())


@celery_app.task(base=BaseTask, bind=True)
def generate_daily_reports(self):
    """Generate daily reports for all active soldiers"""
    import os
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/agniveer_db"
    )
    
    async def _generate():
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy import select
        from models.soldier import Soldier
        
        engine = create_async_engine(db_url)
        
        async with AsyncSession(engine) as session:
            result = await session.execute(
                select(Soldier).where(Soldier.is_active == True)
            )
            soldiers = result.scalars().all()
            
            # Create tasks for each soldier
            tasks = group(
                generate_daily_report.s(soldier.id)
                for soldier in soldiers
            )
            
            result = tasks.apply_async()
            
            return {
                "status": "queued",
                "total_soldiers": len(soldiers),
                "batch_id": result.id
            }
    
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_generate())


@celery_app.task(base=BaseTask, bind=True)
def generate_monthly_reports(self, month: int = None, year: int = None):
    """Generate monthly reports for all active soldiers"""
    from datetime import date
    
    async def _generate():
        import os
        db_url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/agniveer_db"
        )
        
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy import select
        from models.soldier import Soldier
        
        target_month = month or datetime.now().month
        target_year = year or datetime.now().year
        
        engine = create_async_engine(db_url)
        
        async with AsyncSession(engine) as session:
            result = await session.execute(
                select(Soldier).where(Soldier.is_active == True)
            )
            soldiers = result.scalars().all()
            
            # Create tasks
            tasks = group(
                generate_monthly_report.s(soldier.id, target_month, target_year)
                for soldier in soldiers
            )
            
            result = tasks.apply_async()
            
            return {
                "status": "queued",
                "month": target_month,
                "year": target_year,
                "total_soldiers": len(soldiers)
            }
    
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_generate())


@celery_app.task(base=BaseTask, bind=True, max_retries=3)
def generate_monthly_report(self, soldier_id: int, month: int, year: int):
    """Generate monthly report for a specific soldier"""
    
    async def _generate():
        import os
        db_url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/agniveer_db"
        )
        
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy import select, desc
        from datetime import datetime
        from models.soldier import Soldier, TrainingRecord
        from services.report_generator import pdf_generator
        
        engine = create_async_engine(db_url)
        
        async with AsyncSession(engine) as session:
            result = await session.execute(select(Soldier).where(Soldier.id == soldier_id))
            soldier = result.scalar_one_or_none()
            
            if not soldier:
                return {"error": "Soldier not found"}
            
            # Get training records for the month
            start_date = datetime(year, month, 1).date()
            if month == 12:
                end_date = datetime(year + 1, 1, 1).date()
            else:
                end_date = datetime(year, month + 1, 1).date()
            
            result = await session.execute(
                select(TrainingRecord).where(
                    TrainingRecord.soldier_id == soldier_id,
                    TrainingRecord.training_date >= start_date,
                    TrainingRecord.training_date < end_date
                )
            )
            records = result.scalars().all()
            
            # Calculate statistics
            fitness_scores = []
            weapons_scores = []
            mental_scores = []
            overall_scores = []
            
            for record in records:
                if record.endurance_score:
                    fitness_scores.append(record.endurance_score)
                if record.shooting_accuracy:
                    weapons_scores.append(record.shooting_accuracy)
                if record.decision_score:
                    mental_scores.append(record.decision_score)
                if record.overall_score:
                    overall_scores.append(record.overall_score)
            
            performance_summary = {
                "fitness_avg": sum(fitness_scores) / len(fitness_scores) if fitness_scores else 0,
                "weapons_avg": sum(weapons_scores) / len(weapons_scores) if weapons_scores else 0,
                "mental_avg": sum(mental_scores) / len(mental_scores) if mental_scores else 0,
                "overall_avg": sum(overall_scores) / len(overall_scores) if overall_scores else 0,
            }
            
            # Attendance
            total_days = (end_date - start_date).days
            attendance = {
                "total_days": total_days,
                "present": len(records),
                "absent": total_days - len(records),
                "percentage": (len(records) / total_days * 100) if total_days > 0 else 0
            }
            
            # Generate PDF
            pdf_content = pdf_generator.generate_monthly_report(
                soldier_name=soldier.full_name,
                soldier_id=soldier.soldier_id,
                month=month,
                year=year,
                performance_summary=performance_summary,
                attendance=attendance,
                rankings=[]
            )
            
            return {
                "status": "success",
                "soldier_id": soldier_id,
                "month": month,
                "year": year,
                "pdf_size": len(pdf_content)
            }
    
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_generate())





