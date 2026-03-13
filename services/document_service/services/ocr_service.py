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
