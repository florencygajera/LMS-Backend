"""
AI Soldier Performance Prediction Model
Agniveer Sentinel - Machine Learning Layer
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import pickle
import os


class PerformancePredictionModel:
    """ML model for predicting soldier performance"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def prepare_features(self, training_data: pd.DataFrame) -> np.ndarray:
        """Prepare features for training/prediction"""
        features = []
        
        # Numeric features
        if 'running_time_minutes' in training_data.columns:
            features.append(training_data['running_time_minutes'].fillna(0))
        if 'pushups_count' in training_data.columns:
            features.append(training_data['pushups_count'].fillna(0))
        if 'pullups_count' in training_data.columns:
            features.append(training_data['pullups_count'].fillna(0))
        if 'endurance_score' in training_data.columns:
            features.append(training_data['endurance_score'].fillna(0))
        if 'shooting_accuracy' in training_data.columns:
            features.append(training_data['shooting_accuracy'].fillna(0))
        if 'decision_score' in training_data.columns:
            features.append(training_data['decision_score'].fillna(0))
        
        if not features:
            return np.array([])
        
        X = np.column_stack(features)
        return X
    
    def train(self, training_data: pd.DataFrame, target_column: str = 'overall_score'):
        """Train the performance prediction model"""
        if target_column not in training_data.columns:
            raise ValueError(f"Target column {target_column} not found")
        
        X = self.prepare_features(training_data)
        y = training_data[target_column].values
        
        if len(X) == 0 or len(y) == 0:
            raise ValueError("Insufficient training data")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        self.is_trained = True
        
        return {
            "train_score": train_score,
            "test_score": test_score,
            "samples": len(X)
        }
    
    def predict(self, soldier_data: pd.DataFrame) -> dict:
        """Predict soldier performance"""
        if not self.is_trained:
            return {"error": "Model not trained"}
        
        X = self.prepare_features(soldier_data)
        
        if len(X) == 0:
            return {"error": "Invalid data"}
        
        X_scaled = self.scaler.transform(X)
        prediction = self.model.predict(X_scaled)[0]
        
        # Get feature importance
        feature_names = ['running_time', 'pushups', 'pullups', 'endurance', 'shooting', 'decision']
        importance = dict(zip(feature_names, self.model.feature_importances_))
        
        return {
            "predicted_score": float(prediction),
            "confidence": "high" if self.model.score(X_scaled, [prediction]) > 0.8 else "medium",
            "feature_importance": importance
        }
    
    def detect_decline(self, historical_data: pd.DataFrame) -> dict:
        """Detect declining performance trends"""
        if len(historical_data) < 5:
            return {"error": "Insufficient data for trend analysis"}
        
        # Calculate trend
        scores = historical_data['overall_score'].values
        X = np.arange(len(scores)).reshape(-1, 1)
        
        # Simple linear regression for trend
        from sklearn.linear_model import LinearRegression
        trend_model = LinearRegression()
        trend_model.fit(X, scores)
        
        slope = trend_model.coef_[0]
        
        # Determine status
        if slope < -2:
            status = "declining"
            risk_level = "high"
            recommendation = "Immediate intervention required. Consider reduced intensity training."
        elif slope < 0:
            status = "slight_decline"
            risk_level = "medium"
            recommendation = "Monitor closely. Increase recovery periods."
        else:
            status = "improving"
            risk_level = "low"
            recommendation = "Continue current training regimen."
        
        return {
            "status": status,
            "risk_level": risk_level,
            "slope": float(slope),
            "recommendation": recommendation,
            "data_points": len(scores)
        }
    
    def save_model(self, path: str):
        """Save model to disk"""
        if not self.is_trained:
            return False
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'is_trained': self.is_trained
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
        
        return True
    
    def load_model(self, path: str):
        """Load model from disk"""
        if not os.path.exists(path):
            return False
        
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.is_trained = model_data['is_trained']
        
        return True


class InjuryRiskModel:
    """ML model for predicting injury risk"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def train(self, training_data: pd.DataFrame):
        """Train injury risk prediction model"""
        # Features: training load, recovery time, historical injuries
        features = [
            'training_intensity',
            'training_frequency',
            'recovery_days',
            'previous_injuries',
            'sleep_hours',
            'stress_level'
        ]
        
        # Prepare data
        X = training_data[features].fillna(0).values
        y = training_data['injury_occurred'].values
        
        # Scale
        X_scaled = self.scaler.fit_transform(X)
        
        # Train
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
        self.model.fit(X_scaled, y)
        
        self.is_trained = True
        
        return {"accuracy": self.model.score(X_scaled, y)}
    
    def predict_risk(self, soldier_data: dict) -> dict:
        """Predict injury risk"""
        if not self.is_trained:
            return {"error": "Model not trained"}
        
        features = [
            soldier_data.get('training_intensity', 0),
            soldier_data.get('training_frequency', 0),
            soldier_data.get('recovery_days', 0),
            soldier_data.get('previous_injuries', 0),
            soldier_data.get('sleep_hours', 0),
            soldier_data.get('stress_level', 0)
        ]
        
        X = np.array(features).reshape(1, -1)
        X_scaled = self.scaler.transform(X)
        
        probability = self.model.predict_proba(X_scaled)[0][1]
        
        if probability > 0.7:
            risk_level = "HIGH"
            recommendation = "Rest day recommended. High injury risk detected."
        elif probability > 0.4:
            risk_level = "MODERATE"
            recommendation = "Reduce training intensity. Monitor for symptoms."
        else:
            risk_level = "LOW"
            recommendation = "Training can proceed as normal."
        
        return {
            "risk_probability": float(probability),
            "risk_level": risk_level,
            "recommendation": recommendation
        }


# Singleton instances
performance_model = PerformancePredictionModel()
injury_risk_model = InjuryRiskModel()


