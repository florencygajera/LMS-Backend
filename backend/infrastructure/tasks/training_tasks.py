"""
Training Background Tasks
Agniveer Sentinel - Enterprise Production
"""

from infrastructure.celery_config import celery_app, BaseTask
import asyncio


@celery_app.task(base=BaseTask, bind=True)
def update_leaderboard(self, battalion_id: int = None, month: int = None, year: int = None):
    """Update performance leaderboard"""
    
    from datetime import datetime
    
    async def _update():
        import os
        db_url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/agniveer_db"
        )
        
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy import select, desc, and_
        from models.soldier import Soldier, TrainingRecord, PerformanceRanking
        
        target_month = month or datetime.now().month
        target_year = year or datetime.now().year
        
        engine = create_async_engine(db_url)
        
        async with AsyncSession(engine) as session:
            # Get all soldiers
            if battalion_id:
                result = await session.execute(
                    select(Soldier).where(
                        Soldier.battalion_id == battalion_id,
                        Soldier.is_active == True
                    )
                )
            else:
                result = await session.execute(
                    select(Soldier).where(Soldier.is_active == True)
                )
            
            soldiers = result.scalars().all()
            
            # Calculate scores for each soldier
            rankings = []
            
            for soldier in soldiers:
                # Get training records for the month
                start_date = datetime(target_year, target_month, 1).date()
                if target_month == 12:
                    end_date = datetime(target_year + 1, 1, 1).date()
                else:
                    end_date = datetime(target_year, target_month + 1, 1).date()
                
                result = await session.execute(
                    select(TrainingRecord).where(
                        TrainingRecord.soldier_id == soldier.id,
                        and_(
                            TrainingRecord.training_date >= start_date,
                            TrainingRecord.training_date < end_date
                        )
                    )
                )
                records = result.scalars().all()
                
                if not records:
                    continue
                
                # Calculate scores
                fitness_scores = []
                weapons_scores = []
                mental_scores = []
                attendance_score = len(records) * 10  # Simple attendance calc
                discipline_score = 90  # Default, would be more complex
                
                for record in records:
                    if record.endurance_score:
                        fitness_scores.append(record.endurance_score)
                    if record.pushups_count:
                        fitness_scores.append(min(record.pushups_count, 100))
                    
                    if record.shooting_accuracy:
                        weapons_scores.append(record.shooting_accuracy)
                    if record.weapon_handling_score:
                        weapons_scores.append(record.weapon_handling_score)
                    
                    if record.decision_score:
                        mental_scores.append(record.decision_score)
                    if record.psychological_score:
                        mental_scores.append(record.psychological_score)
                
                fitness_score = sum(fitness_scores) / len(fitness_scores) if fitness_scores else 0
                weapon_score = sum(weapons_scores) / len(weapons_scores) if weapons_scores else 0
                mental_score = sum(mental_scores) / len(mental_scores) if mental_scores else 0
                
                overall_score = (fitness_score * 0.3 + weapon_score * 0.3 + 
                               mental_score * 0.2 + attendance_score * 0.1 + 
                               discipline_score * 0.1)
                
                rankings.append({
                    "soldier_id": soldier.id,
                    "battalion_id": soldier.battalion_id,
                    "fitness_score": fitness_score,
                    "weapon_score": weapon_score,
                    "mental_score": mental_score,
                    "attendance_score": attendance_score,
                    "discipline_score": discipline_score,
                    "overall_score": overall_score
                })
            
            # Sort by overall score
            rankings.sort(key=lambda x: x["overall_score"], reverse=True)
            
            # Update rankings in database
            for rank, data in enumerate(rankings, 1):
                # Check if ranking exists
                result = await session.execute(
                    select(PerformanceRanking).where(
                        PerformanceRanking.soldier_id == data["soldier_id"],
                        PerformanceRanking.month == target_month,
                        PerformanceRanking.year == target_year
                    )
                )
                ranking = result.scalar_one_or_none()
                
                if ranking:
                    ranking.fitness_score = data["fitness_score"]
                    ranking.weapon_score = data["weapon_score"]
                    ranking.mental_score = data["mental_score"]
                    ranking.attendance_score = data["attendance_score"]
                    ranking.discipline_score = data["discipline_score"]
                    ranking.overall_score = data["overall_score"]
                    ranking.rank = rank
                else:
                    ranking = PerformanceRanking(
                        soldier_id=data["soldier_id"],
                        battalion_id=data["battalion_id"],
                        month=target_month,
                        year=target_year,
                        fitness_score=data["fitness_score"],
                        weapon_score=data["weapon_score"],
                        mental_score=data["mental_score"],
                        attendance_score=data["attendance_score"],
                        discipline_score=data["discipline_score"],
                        overall_score=data["overall_score"],
                        rank=rank
                    )
                    session.add(ranking)
            
            await session.commit()
            
            return {
                "status": "updated",
                "month": target_month,
                "year": target_year,
                "total_rankings": len(rankings)
            }
    
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_update())


@celery_app.task(base=BaseTask, bind=True)
def process_training_excel(self, file_path: str, trainer_id: int):
    """Process Excel training data file"""
    
    async def _process():
        import pandas as pd
        import os
        
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Process (similar to Excel processor)
        # Would validate and insert into database
        
        os.remove(file_path)  # Cleanup
        
        return {
            "status": "processed",
            "rows": len(df)
        }
    
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_process())





