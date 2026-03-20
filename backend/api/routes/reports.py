"""
Report Service API Endpoints
Agniveer Sentinel - Soldier Management LMS
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional
from datetime import date, datetime
import io

from core.database import get_db
from core.authorization import can_access_soldier_profile
from core.security import get_current_user
from models.base import UserRole
from models.user import User
from models.soldier import Soldier, TrainingRecord, MedicalRecord, Stipend
from services.report_generator import pdf_generator


router = APIRouter()

@router.get("/")
async def report_service_test():
    return {"message": "report service working"}


@router.get("/health")
async def report_health():
    return {"status": "healthy", "service": "reports"}


@router.get("/soldier/{soldier_id}/daily")
async def generate_daily_report(
    soldier_id: int,
    report_date: date,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate daily performance report as PDF"""
    # Verify soldier
    soldier = await can_access_soldier_profile(soldier_id, current_user, db)
    
    # Get training records for the date
    result = await db.execute(
        select(TrainingRecord).where(
            TrainingRecord.soldier_id == soldier_id,
            TrainingRecord.training_date == report_date
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
        elif record.training_type.value == "mental":
            training_data["mental"] = {
                "decision_score": record.decision_score,
                "psychological_score": record.psychological_score
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
        training_date=report_date,
        training_data=training_data
    )
    
    return StreamingResponse(
        io.BytesIO(pdf_content),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=daily_report_{soldier.soldier_id}_{report_date}.pdf"
        }
    )


@router.get("/soldier/{soldier_id}/monthly")
async def generate_monthly_report(
    soldier_id: int,
    month: int,
    year: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate monthly progress report as PDF"""
    # Verify soldier
    soldier = await can_access_soldier_profile(soldier_id, current_user, db)
    
    # Get training records for the month
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()
    
    result = await db.execute(
        select(TrainingRecord).where(
            TrainingRecord.soldier_id == soldier_id,
            TrainingRecord.training_date >= start_date,
            TrainingRecord.training_date < end_date
        )
    )
    records = result.scalars().all()
    
    # Calculate performance summary
    fitness_scores = []
    weapons_scores = []
    mental_scores = []
    overall_scores = []
    
    for record in records:
        if record.endurance_score:
            fitness_scores.append(record.endurance_score)
        if record.pushups_count:
            fitness_scores.append(min(record.pushups_count, 100))
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
    
    # Get rankings
    rankings = []
    # (In production, would query PerformanceRanking table)
    
    # Generate PDF
    pdf_content = pdf_generator.generate_monthly_report(
        soldier_name=soldier.full_name,
        soldier_id=soldier.soldier_id,
        month=month,
        year=year,
        performance_summary=performance_summary,
        attendance=attendance,
        rankings=rankings
    )
    
    return StreamingResponse(
        io.BytesIO(pdf_content),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=monthly_report_{soldier.soldier_id}_{month}_{year}.pdf"
        }
    )


@router.get("/soldier/{soldier_id}/medical")
async def generate_medical_report(
    soldier_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate medical report as PDF"""
    # Verify soldier
    soldier = await can_access_soldier_profile(soldier_id, current_user, db)
    
    # Get medical records
    result = await db.execute(
        select(MedicalRecord).where(
            MedicalRecord.soldier_id == soldier_id,
            MedicalRecord.is_active == True
        ).order_by(desc(MedicalRecord.visit_date))
    )
    records = result.scalars().all()
    
    # Prepare records data
    medical_records = []
    for record in records:
        medical_records.append({
            "visit_date": record.visit_date.strftime("%d-%m-%Y"),
            "doctor_name": record.doctor_name,
            "diagnosis": record.diagnosis,
            "treatment": record.treatment
        })
    
    # Generate PDF
    pdf_content = pdf_generator.generate_medical_report(
        soldier_name=soldier.full_name,
        soldier_id=soldier.soldier_id,
        medical_records=medical_records
    )
    
    return StreamingResponse(
        io.BytesIO(pdf_content),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=medical_report_{soldier.soldier_id}.pdf"
        }
    )


@router.get("/soldier/{soldier_id}/stipend")
async def generate_stipend_report(
    soldier_id: int,
    year: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate stipend report as PDF"""
    # Verify soldier
    soldier = await can_access_soldier_profile(soldier_id, current_user, db)
    
    # Get stipend records
    result = await db.execute(
        select(Stipend).where(
            Stipend.soldier_id == soldier_id,
            Stipend.year == year
        ).order_by(desc(Stipend.month))
    )
    stipends = result.scalars().all()
    
    # Generate PDF
    buffer = io.BytesIO()
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width/2, height - 1*inch, "AGNIVEER SENTINEL")
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height - 1.4*inch, f"STIPEND REPORT - {year}")
    
    # Soldier info
    y = height - 2*inch
    c.setFont("Helvetica", 11)
    c.drawString(1*inch, y, f"Name: {soldier.full_name}")
    y -= 0.3*inch
    c.drawString(1*inch, y, f"Soldier ID: {soldier.soldier_id}")
    y -= 0.3*inch
    c.drawString(1*inch, y, f"Rank: {soldier.rank or 'N/A'}")
    
    # Table header
    y -= 0.6*inch
    c.setFont("Helvetica-Bold", 10)
    c.drawString(1*inch, y, "Month")
    c.drawString(2.5*inch, y, "Base Amount")
    c.drawString(4*inch, y, "Allowances")
    c.drawString(5.5*inch, y, "Deductions")
    c.drawString(7*inch, y, "Net Amount")
    c.drawString(8.5*inch, y, "Status")
    
    y -= 0.2*inch
    c.line(1*inch, y, 9.5*inch, y)
    
    # Table rows
    c.setFont("Helvetica", 9)
    month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    total_net = 0
    for stipend in stipends:
        y -= 0.3*inch
        c.drawString(1*inch, y, month_names[stipend.month])
        c.drawString(2.5*inch, y, f"₹{stipend.base_amount:,.2f}")
        c.drawString(4*inch, y, f"₹{stipend.allowances:,.2f}")
        c.drawString(5.5*inch, y, f"₹{stipend.deductions:,.2f}")
        c.drawString(7*inch, y, f"₹{stipend.net_amount:,.2f}")
        c.drawString(8.5*inch, y, stipend.payment_status.value)
        total_net += stipend.net_amount
    
    # Total
    y -= 0.4*inch
    c.setFont("Helvetica-Bold", 10)
    c.drawString(5.5*inch, y, "Total:")
    c.drawString(7*inch, y, f"₹{total_net:,.2f}")
    
    c.save()
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=stipend_report_{soldier.soldier_id}_{year}.pdf"
        }
    )




