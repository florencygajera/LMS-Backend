"""
ML Prediction Service
Predicts soldier performance risk using RandomForest
"""

import logging
import pickle
from typing import Dict, Any, List
from pathlib import Path
import numpy as np

logger = logging.getLogger("AgniAssist.ML")

try:
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("Scikit-learn not available")


class MLService:
    """ML service for performance prediction"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = Path("agniassist_data/models")
        self.model_path.mkdir(exist_ok=True)
        self.is_trained = False
    
    def initialize(self):
        """Initialize or load model"""
        if not SKLEARN_AVAILABLE:
            logger.warning("Scikit-learn not available")
            return
        
        model_file = self.model_path / "performance_model.pkl"
        
        if model_file.exists():
            try:
                with open(model_file, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data['model']
                    self.scaler = data['scaler']
                    self.is_trained = True
                logger.info("✅ Loaded trained model")
            except Exception as e:
                logger.warning(f"Could not load model: {e}")
                self._train_default_model()
        else:
            self._train_default_model()
    
    def _train_default_model(self):
        """Train a default model with sample data"""
        logger.info("Training default model...")
        
        # Sample training data: [age, bmi, pushups, pullups, run_time, training_days]
        X = np.array([
            [22, 22, 45, 8, 8.5, 20],
            [25, 24, 50, 10, 7.0, 25],
            [28, 26, 40, 6, 9.0, 18],
            [30, 25, 55, 12, 6.5, 28],
            [22, 21, 35, 5, 10.0, 15],
            [27, 23, 48, 9, 7.5, 22],
            [32, 27, 42, 7, 8.8, 20],
            [24, 22, 52, 11, 7.2, 26],
            [26, 24, 46, 8, 8.0, 21],
            [29, 25, 44, 7, 8.2, 19],
            # More samples
            [23, 23, 47, 9, 7.8, 23],
            [31, 26, 43, 7, 8.5, 20],
            [21, 20, 38, 6, 9.5, 16],
            [33, 28, 41, 6, 9.0, 17],
            [25, 23, 49, 10, 7.3, 24],
        ])
        
        # Risk labels: 0=Low, 1=Medium, 2=High
        y = np.array([0, 0, 1, 0, 2, 0, 1, 0, 1, 1, 0, 1, 2, 1, 0])
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
        self.model.fit(X_scaled, y)
        
        # Save model
        self._save_model()
        
        self.is_trained = True
        logger.info("✅ Trained default model")
    
    def _save_model(self):
        """Save model to disk"""
        model_file = self.model_path / "performance_model.pkl"
        with open(model_file, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler
            }, f)
    
    async def predict_risk(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Predict performance risk"""
        if not self.is_trained or self.model is None:
            return {
                "success": False,
                "error": "Model not trained",
                "risk_level": "unknown"
            }
        
        try:
            # Extract features
            feature_names = ['age', 'bmi', 'pushups', 'pullups', 'run_time', 'training_days']
            
            # Get values with defaults
            values = []
            for name in feature_names:
                val = features.get(name, 0)
                values.append(float(val))
            
            # Scale
            X = np.array([values])
            X_scaled = self.scaler.transform(X)
            
            # Predict
            risk_pred = self.model.predict(X_scaled)[0]
            risk_proba = self.model.predict_proba(X_scaled)[0]
            
            # Map to labels
            risk_labels = {0: "Low", 1: "Medium", 2: "High"}
            risk_level = risk_labels.get(risk_pred, "Unknown")
            
            # Generate recommendations
            recommendations = self._generate_recommendations(values, risk_level)
            
            return {
                "success": True,
                "risk_level": risk_level,
                "confidence": float(max(risk_proba)),
                "risk_scores": {
                    "low": float(risk_proba[0]),
                    "medium": float(risk_proba[1]),
                    "high": float(risk_proba[2])
                },
                "recommendations": recommendations,
                "features_used": feature_names
            }
        
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "risk_level": "error"
            }
    
    def _generate_recommendations(self, features: List[float], risk_level: str) -> List[str]:
        """Generate recommendations based on features"""
        age, bmi, pushups, pullups, run_time, training_days = features
        recommendations = []
        
        if risk_level == "High":
            recommendations.append("⚠️ Immediate attention required")
        
        if pushups < 40:
            recommendations.append("Increase daily push-ups to 50+")
        if pullups < 7:
            recommendations.append("Focus on pull-up training - target 10+")
        if run_time > 8.5:
            recommendations.append("Improve running speed - target under 7 min for 1.6km")
        if training_days < 20:
            recommendations.append("Increase training frequency to daily")
        
        if bmi > 25:
            recommendations.append("Monitor weight and maintain healthy BMI")
        
        if not recommendations:
            recommendations.append("Continue current training regime")
        
        return recommendations[:5]  # Limit to 5
    
    async def train_model(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Train model with new data"""
        if not SKLEARN_AVAILABLE:
            return {"success": False, "error": "Scikit-learn not available"}
        
        try:
            X = np.array([[
                d['age'], d['bmi'], d['pushups'], d['pullups'], 
                d['run_time'], d['training_days']
            ] for d in training_data])
            y = np.array([d['risk_label'] for d in training_data])
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate
            train_score = self.model.score(X_train_scaled, y_train)
            test_score = self.model.score(X_test_scaled, y_test)
            
            # Save
            self._save_model()
            self.is_trained = True
            
            return {
                "success": True,
                "train_accuracy": float(train_score),
                "test_accuracy": float(test_score),
                "samples_used": len(training_data)
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton instance
ml_service = MLService()



