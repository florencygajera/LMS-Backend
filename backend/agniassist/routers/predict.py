"""
ML Prediction Router
POST /api/predict
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

try:
    from agniassist.security import verify_token
except ModuleNotFoundError:
    from security import verify_token

router = APIRouter()


class PredictionRequest(BaseModel):
    age: float
    bmi: float
    pushups: int
    pullups: int
    run_time: float  # in minutes
    training_days: int


class TrainingDataRequest(BaseModel):
    training_data: List[Dict[str, Any]]


class PredictionResponse(BaseModel):
    success: bool
    risk_level: str
    confidence: float
    risk_scores: dict
    recommendations: List[str]
    features_used: list
    error: Optional[str] = None


@router.post("/predict", response_model=PredictionResponse)
async def predict_performance(
    request: PredictionRequest,
    user: dict = Depends(verify_token)
):
    """Predict soldier performance risk"""
    from agniassist.services.ml_service import ml_service
    
    try:
        features = request.dict()
        result = await ml_service.predict_risk(features)
        
        return PredictionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/train")
async def train_model(
    request: TrainingDataRequest,
    user: dict = Depends(verify_token)
):
    """Train ML model with new data"""
    from agniassist.services.ml_service import ml_service
    
    try:
        result = await ml_service.train_model(request.training_data)
        
        if result.get("success"):
            return {
                "success": True,
                "message": "Model trained successfully",
                **result
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predict/status")
async def get_model_status(
    user: dict = Depends(verify_token)
):
    """Get ML model status"""
    from agniassist.services.ml_service import ml_service
    
    return {
        "is_trained": ml_service.is_trained,
        "model_available": ml_service.model is not None
    }



