"""
Admit Card Generation Service
Agniveer Sentinel - Phase 1: Recruitment System
"""

import io
import qrcode
from datetime import datetime
from typing import Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


class AdmitCardGenerator:
    """Generate admit cards as PDF"""
    
    def __init__(self):
        self.page_width, self.page_height = A4
    
    def generate_qr_code(self, data: str) -> bytes:
        """Generate QR code as bytes"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    
    def generate_admit_card_pdf(
        self,
        candidate_name: str,
        registration_id: str,
        exam_center: str,
        exam_date: str,
        exam_time: str,
        candidate_photo_url: Optional[str] = None,
    ) -> bytes:
        """Generate admit card PDF"""
        
        # Generate admit card number
        admit_card_number = f"AC-{registration_id}-{datetime.utcnow().strftime('%Y%m%d')}"
        
        # Generate QR code data
        qr_data = f"""
        Agniveer Recruitment - Admit Card
        Registration ID: {registration_id}
        Admit Card Number: {admit_card_number}
        Exam Date: {exam_date}
        Exam Time: {exam_time}
        """
        
        # Create PDF
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Draw border
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.rect(0.5*inch, 0.5*inch, self.page_width - 1*inch, self.page_height - 1*inch)
        
        # Draw inner border
        c.setLineWidth(1)
        c.rect(0.7*inch, 0.7*inch, self.page_width - 1.4*inch, self.page_height - 1.4*inch)
        
        # Header
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(self.page_width/2, self.page_height - 1.2*inch, "AGNIVEER RECRUITMENT")
        
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(self.page_width/2, self.page_height - 1.7*inch, "ADMIT CARD")
        
        c.setFont("Helvetica", 12)
        c.drawCentredString(self.page_width/2, self.page_height - 2.1*inch, "(Common Entrance Test - CET)")
        
        # Separator line
        c.line(1*inch, self.page_height - 2.3*inch, self.page_width - 1*inch, self.page_height - 2.3*inch)
        
        # Candidate Details
        y_position = self.page_height - 2.8*inch
        
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1.2*inch, y_position, "Candidate Details:")
        
        y_position -= 0.4*inch
        c.setFont("Helvetica", 12)
        
        # Name
        c.drawString(1.2*inch, y_position, "Candidate Name:")
        c.drawString(3.2*inch, y_position, candidate_name)
        
        y_position -= 0.35*inch
        # Registration ID
        c.drawString(1.2*inch, y_position, "Registration ID:")
        c.drawString(3.2*inch, y_position, registration_id)
        
        y_position -= 0.35*inch
        # Admit Card Number
        c.drawString(1.2*inch, y_position, "Admit Card Number:")
        c.drawString(3.2*inch, y_position, admit_card_number)
        
        # Separator line
        y_position -= 0.5*inch
        c.line(1*inch, y_position, self.page_width - 1*inch, y_position)
        
        # Exam Details
        y_position -= 0.4*inch
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1.2*inch, y_position, "Exam Details:")
        
        y_position -= 0.4*inch
        c.setFont("Helvetica", 12)
        
        # Exam Center
        c.drawString(1.2*inch, y_position, "Exam Center:")
        c.drawString(3.2*inch, y_position, exam_center)
        
        y_position -= 0.35*inch
        # Exam Date
        c.drawString(1.2*inch, y_position, "Exam Date:")
        c.drawString(3.2*inch, y_position, exam_date)
        
        y_position -= 0.35*inch
        # Exam Time
        c.drawString(1.2*inch, y_position, "Exam Time:")
        c.drawString(3.2*inch, y_position, exam_time)
        
        # QR Code
        qr_bytes = self.generate_qr_code(qr_data)
        qr_image = ImageReader(io.BytesIO(qr_bytes))
        c.drawImage(qr_image, self.page_width - 2.5*inch, self.page_height - 6*inch, width=1.5*inch, height=1.5*inch)
        
        # Instructions
        y_position -= 0.6*inch
        c.line(1*inch, y_position, self.page_width - 1*inch, y_position)
        
        y_position -= 0.4*inch
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1.2*inch, y_position, "Important Instructions:")
        
        y_position -= 0.35*inch
        c.setFont("Helvetica", 10)
        instructions = [
            "1. Bring this admit card to the exam center along with valid photo ID.",
            "2. Reach the exam center at least 30 minutes before the exam start time.",
            "3. No electronic devices are allowed inside the exam hall.",
            "4. Follow all COVID-19 guidelines as issued by the examination authority.",
            "5. Candidate must carry their own pen and pencil.",
        ]
        
        for instruction in instructions:
            c.drawString(1.2*inch, y_position, instruction)
            y_position -= 0.25*inch
        
        # Footer
        c.setFont("Helvetica", 8)
        c.drawCentredString(self.page_width/2, 1*inch, "This is a computer-generated document. No signature is required.")
        c.drawCentredString(self.page_width/2, 0.8*inch, f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} IST")
        
        c.save()
        buffer.seek(0)
        
        return buffer.getvalue(), admit_card_number


class NotificationService:
    """Send admit card via email and SMS"""
    
    def __init__(self):
        # Would initialize SMTP and SMS clients here
        pass
    
    async def send_admit_card_email(
        self,
        email: str,
        candidate_name: str,
        admit_card_pdf: bytes,
        registration_id: str
    ) -> bool:
        """Send admit card via email"""
        # Implementation would use aiohttp/smtp
        # For now, return success
        print(f"Would send email to {email} with admit card for {candidate_name} ({registration_id})")
        return True
    
    async def send_admit_card_sms(
        self,
        phone_number: str,
        candidate_name: str,
        registration_id: str,
        exam_date: str
    ) -> bool:
        """Send admit card notification via SMS"""
        # Implementation would use SMS API
        message = f"Admit Card for Agniveer Recruitment - CET. Registration: {registration_id}, Exam Date: {exam_date}. Check your email for the admit card."
        print(f"Would send SMS to {phone_number}: {message}")
        return True


# Singleton instances
admit_card_generator = AdmitCardGenerator()
notification_service = NotificationService()
