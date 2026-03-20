"""
PDF Report Generation Service
Agniveer Sentinel - Performance Reports
"""

import io
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


class PDFReportGenerator:
    """Generate PDF reports for soldiers"""
    
    def __init__(self):
        self.page_width, self.page_height = A4
    
    def _draw_header(self, c: canvas.Canvas, title: str, subtitle: str = None):
        """Draw report header"""
        # Border
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.rect(0.5*inch, 0.5*inch, self.page_width - 1*inch, self.page_height - 1*inch)
        
        # Title
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(self.page_width/2, self.page_height - 1*inch, "AGNIVEER SENTINEL")
        
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(self.page_width/2, self.page_height - 1.4*inch, title)
        
        if subtitle:
            c.setFont("Helvetica", 10)
            c.drawCentredString(self.page_width/2, self.page_height - 1.7*inch, subtitle)
        
        # Line
        c.line(1*inch, self.page_height - 1.9*inch, self.page_width - 1*inch, self.page_height - 1.9*inch)
        
        return self.page_height - 2.2*inch
    
    def _draw_footer(self, c: canvas.Canvas):
        """Draw report footer"""
        c.setFont("Helvetica", 8)
        c.drawCentredString(self.page_width/2, 0.7*inch, f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} IST")
        c.drawCentredString(self.page_width/2, 0.5*inch, "Agniveer Sentinel - Military Training Platform")
    
    def generate_daily_performance_report(
        self,
        soldier_name: str,
        soldier_id: str,
        training_date: date,
        training_data: Dict[str, Any]
    ) -> bytes:
        """Generate daily performance report"""
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Header
        y_position = self._draw_header(
            c,
            "DAILY TRAINING PERFORMANCE REPORT",
            f"Date: {training_date.strftime('%d-%m-%Y')}"
        )
        
        # Soldier Info
        y_position -= 0.5*inch
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1*inch, y_position, "Soldier Details:")
        
        y_position -= 0.3*inch
        c.setFont("Helvetica", 11)
        c.drawString(1.2*inch, y_position, f"Name: {soldier_name}")
        
        y_position -= 0.25*inch
        c.drawString(1.2*inch, y_position, f"Soldier ID: {soldier_id}")
        
        # Training Data
        y_position -= 0.5*inch
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1*inch, y_position, "Training Performance:")
        
        y_position -= 0.4*inch
        
        # Fitness
        if "fitness" in training_data:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(1.2*inch, y_position, "Fitness Training:")
            y_position -= 0.3*inch
            
            c.setFont("Helvetica", 10)
            fitness = training_data["fitness"]
            if fitness.get("running_time"):
                c.drawString(1.4*inch, y_position, f"Running Time: {fitness['running_time']} minutes")
                y_position -= 0.2*inch
            if fitness.get("pushups"):
                c.drawString(1.4*inch, y_position, f"Push-ups: {fitness['pushups']} count")
                y_position -= 0.2*inch
            if fitness.get("endurance_score"):
                c.drawString(1.4*inch, y_position, f"Endurance Score: {fitness['endurance_score']}/100")
                y_position -= 0.2*inch
            
            y_position -= 0.2*inch
        
        # Weapons
        if "weapons" in training_data:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(1.2*inch, y_position, "Weapons Training:")
            y_position -= 0.3*inch
            
            c.setFont("Helvetica", 10)
            weapons = training_data["weapons"]
            if weapons.get("shooting_accuracy"):
                c.drawString(1.4*inch, y_position, f"Shooting Accuracy: {weapons['shooting_accuracy']}%")
                y_position -= 0.2*inch
            if weapons.get("weapon_handling"):
                c.drawString(1.4*inch, y_position, f"Weapon Handling: {weapons['weapon_handling']}/100")
                y_position -= 0.2*inch
            
            y_position -= 0.2*inch
        
        # Mental
        if "mental" in training_data:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(1.2*inch, y_position, "Mental Training:")
            y_position -= 0.3*inch
            
            c.setFont("Helvetica", 10)
            mental = training_data["mental"]
            if mental.get("decision_score"):
                c.drawString(1.4*inch, y_position, f"Decision Score: {mental['decision_score']}/100")
                y_position -= 0.2*inch
            if mental.get("psychological_score"):
                c.drawString(1.4*inch, y_position, f"Psychological Score: {mental['psychological_score']}/100")
                y_position -= 0.2*inch
        
        # Overall Score
        if training_data.get("overall_score"):
            y_position -= 0.5*inch
            c.setFont("Helvetica-Bold", 12)
            c.drawString(1*inch, y_position, f"Overall Score: {training_data['overall_score']}/100")
        
        # Remarks
        if training_data.get("remarks"):
            y_position -= 0.5*inch
            c.setFont("Helvetica-Bold", 11)
            c.drawString(1*inch, y_position, "Trainer Remarks:")
            y_position -= 0.25*inch
            c.setFont("Helvetica", 10)
            c.drawString(1.2*inch, y_position, training_data["remarks"])
        
        # Footer
        self._draw_footer(c)
        
        c.save()
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_monthly_report(
        self,
        soldier_name: str,
        soldier_id: str,
        month: int,
        year: int,
        performance_summary: Dict[str, Any],
        attendance: Dict[str, Any],
        rankings: List[Dict[str, Any]]
    ) -> bytes:
        """Generate monthly progress report"""
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        month_names = ["", "January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]
        
        # Header
        y_position = self._draw_header(
            c,
            "MONTHLY PROGRESS REPORT",
            f"{month_names[month]} {year}"
        )
        
        # Soldier Info
        y_position -= 0.5*inch
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1*inch, y_position, "Soldier Details:")
        
        y_position -= 0.3*inch
        c.setFont("Helvetica", 11)
        c.drawString(1.2*inch, y_position, f"Name: {soldier_name}")
        
        y_position -= 0.25*inch
        c.drawString(1.2*inch, y_position, f"Soldier ID: {soldier_id}")
        
        # Performance Summary
        y_position -= 0.5*inch
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1*inch, y_position, "Performance Summary:")
        
        y_position -= 0.4*inch
        c.setFont("Helvetica", 10)
        
        if "fitness_avg" in performance_summary:
            c.drawString(1.2*inch, y_position, f"Fitness Average: {performance_summary['fitness_avg']:.1f}/100")
            y_position -= 0.2*inch
        
        if "weapons_avg" in performance_summary:
            c.drawString(1.2*inch, y_position, f"Weapons Average: {performance_summary['weapons_avg']:.1f}/100")
            y_position -= 0.2*inch
        
        if "mental_avg" in performance_summary:
            c.drawString(1.2*inch, y_position, f"Mental Score Average: {performance_summary['mental_avg']:.1f}/100")
            y_position -= 0.2*inch
        
        if "overall_avg" in performance_summary:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(1.2*inch, y_position, f"Overall Average: {performance_summary['overall_avg']:.1f}/100")
            y_position -= 0.3*inch
        
        # Attendance
        y_position -= 0.4*inch
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1*inch, y_position, "Attendance:")
        
        y_position -= 0.3*inch
        c.setFont("Helvetica", 10)
        c.drawString(1.2*inch, y_position, f"Total Days: {attendance.get('total_days', 0)}")
        y_position -= 0.2*inch
        c.drawString(1.2*inch, y_position, f"Present: {attendance.get('present', 0)}")
        y_position -= 0.2*inch
        c.drawString(1.2*inch, y_position, f"Absent: {attendance.get('absent', 0)}")
        y_position -= 0.2*inch
        c.drawString(1.2*inch, y_position, f"Attendance Percentage: {attendance.get('percentage', 0):.1f}%")
        
        # Rankings
        if rankings:
            y_position -= 0.5*inch
            c.setFont("Helvetica-Bold", 12)
            c.drawString(1*inch, y_position, "Daily Rankings:")
            
            y_position -= 0.3*inch
            c.setFont("Helvetica", 9)
            
            for rank in rankings[:5]:  # Top 5
                c.drawString(
                    1.2*inch, y_position,
                    f"{rank.get('date')}: Rank #{rank.get('rank')} - Score: {rank.get('score', 0):.1f}"
                )
                y_position -= 0.2*inch
        
        # Footer
        self._draw_footer(c)
        
        c.save()
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_medical_report(
        self,
        soldier_name: str,
        soldier_id: str,
        medical_records: List[Dict[str, Any]]
    ) -> bytes:
        """Generate medical report"""
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Header
        y_position = self._draw_header(c, "MEDICAL RECORD REPORT")
        
        # Soldier Info
        y_position -= 0.5*inch
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1*inch, y_position, "Soldier Details:")
        
        y_position -= 0.3*inch
        c.setFont("Helvetica", 11)
        c.drawString(1.2*inch, y_position, f"Name: {soldier_name}")
        
        y_position -= 0.25*inch
        c.drawString(1.2*inch, y_position, f"Soldier ID: {soldier_id}")
        
        # Medical Records
        y_position -= 0.5*inch
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1*inch, y_position, "Medical History:")
        
        for record in medical_records:
            y_position -= 0.4*inch
            
            c.setFont("Helvetica-Bold", 10)
            c.drawString(1.2*inch, y_position, f"Date: {record.get('visit_date')}")
            
            y_position -= 0.2*inch
            c.setFont("Helvetica", 10)
            c.drawString(1.3*inch, y_position, f"Doctor: {record.get('doctor_name')}")
            
            if record.get('diagnosis'):
                y_position -= 0.2*inch
                c.drawString(1.3*inch, y_position, f"Diagnosis: {record.get('diagnosis')}")
            
            if record.get('treatment'):
                y_position -= 0.2*inch
                # Wrap text
                treatment = record.get('treatment', '')
                if len(treatment) > 80:
                    treatment = treatment[:80] + "..."
                c.drawString(1.3*inch, y_position, f"Treatment: {treatment}")
        
        # Footer
        self._draw_footer(c)
        
        c.save()
        buffer.seek(0)
        return buffer.getvalue()


# Singleton instance
pdf_generator = PDFReportGenerator()





