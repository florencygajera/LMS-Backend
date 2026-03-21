from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User
from models.soldier import PerformanceRanking
from typing import Tuple, Dict

class ContextService:
    async def get_user_context(self, user_id: int, db: AsyncSession) -> Tuple[Dict, str]:
        # Fetch fundamental user data
        user_query = await db.execute(select(User).where(User.id == user_id))
        user = user_query.scalar_one_or_none()
        
        if not user:
            return {"error": "User profile not found"}, "No prediction available."
            
        user_data = {
            "name": user.full_name,
            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
            "status": "Active" if user.is_active else "Inactive",
        }
        
        # Discover specific contextual rankings
        try:
            perf_query = await db.execute(
                select(PerformanceRanking)
                .where(PerformanceRanking.soldier_id == user_id)
                .order_by(PerformanceRanking.created_at.desc())
            )
            ranking = perf_query.scalars().first()
            if ranking:
                user_data.update({
                    "fitness_score": ranking.fitness_score,
                    "attendance_score": ranking.attendance_score,
                    "overall_score": ranking.overall_score
                })
        except Exception:
            pass # Ignore if not a soldier entity
            
        prediction = self._run_ml_prediction(user_data)
        
        return user_data, prediction

    def _run_ml_prediction(self, user_data: dict) -> str:
        # Contextual ML Simulator for Risk Prediction
        if "overall_score" in user_data:
            score = user_data["overall_score"]
            if score < 50:
                return "Risk Level: HIGH - Needs immediate training intervention."
            elif score < 75:
                return "Risk Level: MEDIUM - Consistent progression required."
            return "Risk Level: LOW - Excellent performance metrics."
            
        return "Risk Level: UNKNOWN - Insufficient training data."

context_service = ContextService()
