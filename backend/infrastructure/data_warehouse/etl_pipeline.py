"""
Data Warehouse ETL Pipeline
Agniveer Sentinel - Analytics Layer
"""

from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine
import os


class ETLPipeline:
    """Extract, Transform, Load pipeline for data warehouse"""
    
    def __init__(self):
        self.source_db = os.getenv("DATABASE_URL")
        self.warehouse_db = os.getenv("WAREHOUSE_URL")
        
    def extract_recruitment_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Extract recruitment data from operational DB"""
        query = f"""
            SELECT 
                c.id,
                c.registration_id,
                c.full_name,
                c.date_of_birth,
                c.gender,
                c.education_qualification,
                c.application_status,
                c.created_at,
                a.recruitment_batch,
                a.force_type
            FROM candidates c
            LEFT JOIN applications a ON c.id = a.candidate_id
            WHERE c.created_at BETWEEN '{start_date}' AND '{end_date}'
        """
        
        engine = create_engine(self.source_db)
        df = pd.read_sql(query, engine)
        
        return df
    
    def extract_training_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Extract training data from operational DB"""
        query = f"""
            SELECT 
                s.id as soldier_id,
                s.soldier_id,
                s.full_name,
                s.battalion_id,
                t.training_date,
                t.training_type,
                t.running_time_minutes,
                t.pushups_count,
                t.endurance_score,
                t.shooting_accuracy,
                t.overall_score
            FROM soldiers s
            JOIN training_records t ON s.id = t.soldier_id
            WHERE t.training_date BETWEEN '{start_date}' AND '{end_date}'
        """
        
        engine = create_engine(self.source_db)
        df = pd.read_sql(query, engine)
        
        return df
    
    def transform_recruitment_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform recruitment data for analytics"""
        
        # Calculate age at application
        df['application_date'] = pd.to_datetime(df['created_at'])
        df['date_of_birth'] = pd.to_datetime(df['date_of_birth'])
        df['age_at_application'] = (
            (df['application_date'] - df['date_of_birth']).dt.days / 365.25
        ).round(1)
        
        # Add derived features
        df['age_group'] = pd.cut(
            df['age_at_application'],
            bins=[0, 21, 25, 30, 35, 100],
            labels=['18-21', '22-25', '26-30', '31-35', '35+']
        )
        
        # Convert status to binary
        df['selected'] = df['application_status'].apply(
            lambda x: 1 if x == 'selected' else 0
        )
        
        return df
    
    def transform_training_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform training data for analytics"""
        
        # Calculate aggregates
        df['training_date'] = pd.to_datetime(df['training_date'])
        
        # Add time-based features
        df['day_of_week'] = df['training_date'].dt.day_name()
        df['week_of_year'] = df['training_date'].dt.isocalendar().week
        df['month'] = df['training_date'].dt.month
        
        # Fill missing values
        df['running_time_minutes'] = df['running_time_minutes'].fillna(0)
        df['pushups_count'] = df['pushups_count'].fillna(0)
        df['endurance_score'] = df['endurance_score'].fillna(0)
        df['shooting_accuracy'] = df['shooting_accuracy'].fillna(0)
        df['overall_score'] = df['overall_score'].fillna(0)
        
        return df
    
    def load_to_warehouse(self, df: pd.DataFrame, table_name: str):
        """Load transformed data to warehouse"""
        
        warehouse_engine = create_engine(self.warehouse_db)
        
        # Append to warehouse table
        df.to_sql(
            table_name,
            warehouse_engine,
            if_exists='append',
            index=False
        )
        
        print(f"Loaded {len(df)} rows to {table_name}")
    
    def run_full_etl(self):
        """Run complete ETL pipeline"""
        # Get last 30 days of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Recruitment ETL
        print("Extracting recruitment data...")
        recruitment_df = self.extract_recruitment_data(start_date, end_date)
        
        print("Transforming recruitment data...")
        recruitment_df = self.transform_recruitment_data(recruitment_df)
        
        print("Loading recruitment data...")
        self.load_to_warehouse(recruitment_df, 'dim_recruitment')
        
        # Training ETL
        print("Extracting training data...")
        training_df = self.extract_training_data(start_date, end_date)
        
        print("Transforming training data...")
        training_df = self.transform_training_data(training_df)
        
        print("Loading training data...")
        self.load_to_warehouse(training_df, 'fact_training')
        
        print("ETL pipeline completed!")


class AnalyticsService:
    """Service for generating analytics queries"""
    
    @staticmethod
    def get_recruitment_trends(warehouse_db: str, months: int = 6):
        """Get recruitment trends"""
        query = f"""
            SELECT 
                DATE_TRUNC('month', application_date) as month,
                COUNT(*) as total_applications,
                SUM(selected) as selections,
                ROUND(SUM(selected)::numeric / COUNT(*)::numeric * 100, 2) as selection_rate,
                AVG(age_at_application) as avg_age
            FROM dim_recruitment
            WHERE application_date >= CURRENT_DATE - INTERVAL '{months} months'
            GROUP BY DATE_TRUNC('month', application_date)
            ORDER BY month
        """
        
        engine = create_engine(warehouse_db)
        df = pd.read_sql(query, engine)
        
        return df.to_dict(orient='records')
    
    @staticmethod
    def get_training_performance(warehouse_db: str, battalion_id: int = None):
        """Get training performance analytics"""
        query = """
            SELECT 
                s.battalion_id,
                s.soldier_id,
                s.full_name,
                COUNT(*) as training_days,
                AVG(t.overall_score) as avg_score,
                MAX(t.overall_score) as best_score,
                MIN(t.overall_score) as lowest_score,
                AVG(t.shooting_accuracy) as avg_accuracy,
                AVG(t.endurance_score) as avg_endurance
            FROM fact_training t
            JOIN dim_soldiers s ON t.soldier_id = s.soldier_id
        """
        
        if battalion_id:
            query += f" WHERE s.battalion_id = {battalion_id}"
        
        query += " GROUP BY s.battalion_id, s.soldier_id, s.full_name"
        
        engine = create_engine(warehouse_db)
        df = pd.read_sql(query, engine)
        
        return df.to_dict(orient='records')
    
    @staticmethod
    def get_injury_risk_analysis(warehouse_db: str):
        """Get injury risk patterns"""
        query = """
            SELECT 
                training_type,
                COUNT(*) as total_sessions,
                AVG(overall_score) as avg_performance,
                -- This would correlate with injury data
                0 as injury_count
            FROM fact_training
            GROUP BY training_type
        """
        
        engine = create_engine(warehouse_db)
        df = pd.read_sql(query, engine)
        
        return df.to_dict(orient='records')





