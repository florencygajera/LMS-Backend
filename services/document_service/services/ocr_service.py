"""
OCR Service for Document Processing
Agniveer Sentinel - Document Processing Pipeline
"""

import io
import cv2
import numpy as np
from typing import Dict, Any, Optional
import pytesseract
from PIL import Image


class OCRService:
    """OCR processing for documents"""
    
    def __init__(self, tesseract_path: Optional[str] = None):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    def preprocess_image(self, image_bytes: bytes) -> np.ndarray:
        """Preprocess image for better OCR results"""
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding to improve text readability
        _, thresholded = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Remove noise
        denoised = cv2.fastNlMeansDenoising(thresholded, None, 10, 7, 21)
        
        # Sharpen image
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(denoised, -1, kernel)
        
        return sharpened
    
    def extract_text(self, image_bytes: bytes) -> str:
        """Extract text from image using OCR"""
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image_bytes)
            
            # Extract text
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(
                processed_image,
                config=custom_config,
                lang='eng'
            )
            
            return text.strip()
        
        except Exception as e:
            print(f"OCR Error: {str(e)}")
            return ""
    
    def extract_aadhaar_data(self, ocr_text: str) -> Dict[str, Any]:
        """Extract Aadhaar card data from OCR text"""
        data = {
            "aadhaar_number": None,
            "name": None,
            "dob": None,
            "gender": None,
            "address": None
        }
        
        lines = ocr_text.split('\n')
        
        # Extract Aadhaar number (12 digits)
        import re
        aadhaar_pattern = r'\d{4}\s?\d{4}\s?\d{4}'
        for line in lines:
            match = re.search(aadhaar_pattern, line)
            if match:
                data["aadhaar_number"] = match.group().replace(' ', '')
                break
        
        # Extract name (usually after "Name" keyword)
        for i, line in enumerate(lines):
            if "name" in line.lower() and i + 1 < len(lines):
                data["name"] = lines[i + 1].strip()
                break
        
        # Extract DOB
        dob_pattern = r'\d{2}/\d{2}/\d{4}'
        for line in lines:
            match = re.search(dob_pattern, line)
            if match:
                data["dob"] = match.group()
                break
        
        # Extract gender
        for line in lines:
            if "male" in line.lower():
                data["gender"] = "Male"
                break
            elif "female" in line.lower():
                data["gender"] = "Female"
                break
        
        # Extract address (lines after "Address")
        address_lines = []
        for i, line in enumerate(lines):
            if "address" in line.lower():
                address_lines = lines[i+1:i+5]
                break
        
        if address_lines:
            data["address"] = " ".join([l.strip() for l in address_lines if l.strip()])
        
        return data
    
    def extract_education_data(self, ocr_text: str) -> Dict[str, Any]:
        """Extract education certificate data from OCR text"""
        data = {
            "name": None,
            "course": None,
            "institution": None,
            "year": None,
            "percentage": None,
            "grade": None
        }
        
        lines = [l.strip() for l in ocr_text.split('\n') if l.strip()]
        
        # Extract name (usually first significant line)
        for line in lines[:5]:
            if len(line) > 3 and not any(c.isdigit() for c in line):
                data["name"] = line
                break
        
        # Extract course/degree
        for line in lines:
            keywords = ["bachelor", "master", "diploma", "degree", "certificate"]
            if any(kw in line.lower() for kw in keywords):
                data["course"] = line
                break
        
        # Extract year
        import re
        year_pattern = r'(19|20)\d{2}'
        for line in lines:
            match = re.search(year_pattern, line)
            if match:
                data["year"] = int(match.group())
                break
        
        # Extract percentage/grade
        percent_pattern = r'(\d+\.?\d*)%'
        for line in lines:
            match = re.search(percent_pattern, line)
            if match:
                data["percentage"] = float(match.group(1))
                break
        
        return data
    
    def extract_medical_data(self, ocr_text: str) -> Dict[str, Any]:
        """Extract medical report data from OCR text"""
        data = {
            "patient_name": None,
            "doctor_name": None,
            "diagnosis": None,
            "date": None,
            "recommendations": []
        }
        
        lines = [l.strip() for l in ocr_text.split('\n') if l.strip()]
        
        # Extract patient name
        for line in lines[:5]:
            if "name" in line.lower() and len(line) > 20:
                parts = line.split(':')
                if len(parts) > 1:
                    data["patient_name"] = parts[1].strip()
        
        # Extract doctor name
        for line in lines:
            if "doctor" in line.lower() or "dr." in line.lower():
                parts = line.split(':')
                if len(parts) > 1:
                    data["doctor_name"] = parts[1].strip()
                else:
                    data["doctor_name"] = line.replace("Doctor", "").replace("Dr.", "").strip()
        
        # Extract diagnosis
        for i, line in enumerate(lines):
            if "diagnosis" in line.lower() or "complaint" in line.lower():
                if i + 1 < len(lines):
                    data["diagnosis"] = lines[i + 1]
        
        # Extract date
        import re
        date_pattern = r'\d{2}-\d{2}-\d{4}'
        for line in lines:
            match = re.search(date_pattern, line)
            if match:
                data["date"] = match.group()
                break
        
        return data
    
    async def process_document(
        self,
        document_type: str,
        file_content: bytes
    ) -> Dict[str, Any]:
        """Process document based on type"""
        
        # Extract text
        ocr_text = self.extract_text(file_content)
        
        if not ocr_text:
            return {
                "success": False,
                "error": "Could not extract text from document",
                "text": None,
                "parsed_data": None
            }
        
        # Parse based on document type
        parsed_data = None
        
        if document_type == "aadhaar":
            parsed_data = self.extract_aadhaar_data(ocr_text)
        elif document_type in ["education", "certificate"]:
            parsed_data = self.extract_education_data(ocr_text)
        elif document_type in ["medical", "prescription"]:
            parsed_data = self.extract_medical_data(ocr_text)
        
        return {
            "success": True,
            "text": ocr_text,
            "parsed_data": parsed_data
        }


# Singleton instance
ocr_service = OCRService()
