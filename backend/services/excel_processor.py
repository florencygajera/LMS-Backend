"""
Training Excel Processing Service
Agniveer Sentinel - Phase 2: Soldier Management LMS
"""

import pandas as pd
import io
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.soldier import Soldier, TrainingRecord
from models.base import TrainingType


class ExcelTrainingProcessor:
    """Process Excel files for training data"""
    
    # Expected columns
    REQUIRED_COLUMNS = ["Soldier_ID", "Date"]
    OPTIONAL_COLUMNS = [
        "Running_Time", "Pushups", "Pullups", "Endurance_Score", "BMI",
        "Strategy_Exercises", "Decision_Score", "Psychological_Score",
        "Shooting_Accuracy", "Weapon_Handling", "Combat_Drill", "Trainer_Remarks"
    ]
    
    def validate_dataframe(self, df: pd.DataFrame) -> tuple[bool, str]:
        """Validate the uploaded Excel file"""
        # Check required columns
        missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            return False, f"Missing required columns: {', '.join(missing_cols)}"
        
        # Check if empty
        if df.empty:
            return False, "Excel file is empty"
        
        return True, ""
    
    def validate_row(self, row: pd.Series, soldier_ids: set) -> tuple[bool, str]:
        """Validate a single row of data"""
        # Check soldier ID exists
        if row["Soldier_ID"] not in soldier_ids:
            return False, f"Soldier ID {row['Soldier_ID']} not found"
        
        # Check date format
        try:
            if isinstance(row["Date"], str):
                datetime.strptime(row["Date"], "%Y-%m-%d")
        except ValueError:
            return False, f"Invalid date format: {row['Date']}"
        
        # Validate numeric fields
        numeric_fields = [
            "Running_Time", "Pushups", "Pullups", "Endurance_Score", "BMI",
            "Strategy_Exercises", "Decision_Score", "Psychological_Score",
            "Shooting_Accuracy", "Weapon_Handling", "Combat_Drill"
        ]
        
        for field in numeric_fields:
            if field in row and pd.notna(row[field]):
                try:
                    float(row[field])
                except (ValueError, TypeError):
                    return False, f"Invalid numeric value for {field}: {row[field]}"
        
        return True, ""
    
    async def process_excel(
        self,
        file_content: bytes,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Process Excel file and update training database"""
        
        # Read Excel file
        df = pd.read_excel(io.BytesIO(file_content))
        
        # Validate
        is_valid, error_msg = self.validate_dataframe(df)
        if not is_valid:
            return {"success": False, "error": error_msg, "processed": 0, "failed": 0}
        
        # Get all soldier IDs
        result = await db.execute(select(Soldier.soldier_id))
        soldier_ids = set([row[0] for row in result.all()])
        
        # Process rows
        processed = 0
        failed = 0
        errors = []
        
        for index, row in df.iterrows():
            is_valid, error_msg = self.validate_row(row, soldier_ids)
            
            if not is_valid:
                failed += 1
                errors.append(f"Row {index + 2}: {error_msg}")
                continue
            
            try:
                # Get soldier
                result = await db.execute(
                    select(Soldier).where(Soldier.soldier_id == row["Soldier_ID"])
                )
                soldier = result.scalar_one_or_none()
                
                if not soldier:
                    failed += 1
                    errors.append(f"Row {index + 2}: Soldier not found")
                    continue
                
                # Parse date
                training_date = row["Date"]
                if isinstance(training_date, str):
                    training_date = datetime.strptime(training_date, "%Y-%m-%d").date()
                elif isinstance(training_date, datetime):
                    training_date = training_date.date()
                
                # Determine training type based on data
                training_type = self._determine_training_type(row)
                
                # Create training record
                record = TrainingRecord(
                    soldier_id=soldier.id,
                    training_date=training_date,
                    training_type=training_type,
                    running_time_minutes=row.get("Running_Time"),
                    pushups_count=int(row["Pushups"]) if pd.notna(row.get("Pushups")) else None,
                    pullups_count=int(row["Pullups"]) if pd.notna(row.get("Pullups")) else None,
                    endurance_score=row.get("Endurance_Score"),
                    bmi=row.get("BMI"),
                    strategy_exercises=row.get("Strategy_Exercises"),
                    decision_score=row.get("Decision_Score"),
                    psychological_score=row.get("Psychological_Score"),
                    shooting_accuracy=row.get("Shooting_Accuracy"),
                    weapon_handling_score=row.get("Weapon_Handling"),
                    combat_drill_score=row.get("Combat_Drill"),
                    remarks=row.get("Trainer_Remarks"),
                )
                
                # Calculate overall score
                record.overall_score = self._calculate_overall_score(record)
                
                db.add(record)
                processed += 1
                
            except Exception as e:
                failed += 1
                errors.append(f"Row {index + 2}: {str(e)}")
        
        # Commit all records
        await db.commit()
        
        return {
            "success": True,
            "processed": processed,
            "failed": failed,
            "errors": errors
        }
    
    def _determine_training_type(self, row: pd.Series) -> TrainingType:
        """Determine training type based on data"""
        # Check if fitness data
        if pd.notna(row.get("Running_Time")) or pd.notna(row.get("Pushups")):
            return TrainingType.FITNESS
        
        # Check if mental training
        if pd.notna(row.get("Strategy_Exercises")) or pd.notna(row.get("Decision_Score")):
            return TrainingType.MENTAL
        
        # Check if weapons training
        if pd.notna(row.get("Shooting_Accuracy")) or pd.notna(row.get("Weapon_Handling")):
            return TrainingType.WEAPONS
        
        return TrainingType.FITNESS
    
    def _calculate_overall_score(self, record: TrainingRecord) -> Optional[float]:
        """Calculate overall training score"""
        scores = []
        
        # Fitness score
        if record.endurance_score:
            scores.append(record.endurance_score)
        if record.pushups_count:
            # Normalize pushups (max 100 pushups = 100 score)
            scores.append(min(record.pushups_count, 100))
        
        # Mental score
        if record.decision_score:
            scores.append(record.decision_score)
        if record.psychological_score:
            scores.append(record.psychological_score)
        
        # Weapons score
        if record.shooting_accuracy:
            scores.append(record.shooting_accuracy)
        if record.weapon_handling_score:
            scores.append(record.weapon_handling_score)
        
        if scores:
            return sum(scores) / len(scores)
        
        return None


# Singleton instance
excel_processor = ExcelTrainingProcessor()




