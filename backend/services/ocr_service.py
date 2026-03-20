"""
OCR Document Processing Service
Extracts text from images using local OCR
"""

import logging
from typing import Dict, Any, Optional, List
import re
from pathlib import Path
import numpy as np

logger = logging.getLogger("AgniAssist.OCR")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV not available")


class OCRService:
    """OCR service for document text extraction"""
    
    def __init__(self):
        self.is_initialized = False
        self._load_models()
    
    def _load_models(self):
        """Load OCR models"""
        # Try PaddleOCR first
        try:
            from paddleocr import PaddleOCR
            self.paddle_ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            logger.info("✅ PaddleOCR loaded")
            self.ocr_type = "paddle"
        except ImportError:
            try:
                # Fallback to Tesseract
                import pytesseract
                self.tesseract = pytesseract
                logger.info("✅ Tesseract OCR loaded")
                self.ocr_type = "tesseract"
            except ImportError:
                logger.warning("No OCR engine available")
                self.ocr_type = None
        
        # Try EasyOCR
        try:
            import easyocr
            self.easy_reader = easyocr.Reader(['en'])
            logger.info("✅ EasyOCR loaded")
            self.ocr_type = "easyocr"
        except:
            pass
        
        self.is_initialized = True
    
    async def process_image(self, image_data: bytes) -> Dict[str, Any]:
        """Process image and extract text"""
        if not self.ocr_type:
            return {
                "success": False,
                "error": "No OCR engine available. Please install PaddleOCR, Tesseract, or EasyOCR.",
                "text": "",
                "confidence": 0.0
            }
        
        # Save temp image
        temp_path = Path("agniassist_data/temp")
        temp_path.mkdir(exist_ok=True)
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as f:
            f.write(image_data)
            temp_file = f.name
        
        try:
            # Preprocess image
            processed_image = self._preprocess_image(temp_file)
            
            # Extract text based on available OCR
            if self.ocr_type == "paddle":
                result = self.paddle_ocr.ocr(processed_image, cls=True)
                text = "\n".join([line[1][0] for line in result[0] if line])
                confidence = np.mean([line[1][1] for line in result[0]]) if result[0] else 0
            elif self.ocr_type == "easyocr":
                result = self.easy_reader.readtext(processed_image)
                text = "\n".join([detection[1] for detection in result])
                confidence = np.mean([detection[2] for detection in result]) if result else 0
            else:
                # Tesseract fallback
                import pytesseract
                from PIL import Image
                img = Image.open(processed_image)
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                text = pytesseract.image_to_string(img)
                confidences = [int(conf) for conf in data['conf'] if conf != '-1']
                confidence = np.mean(confidences) / 100.0 if confidences else 0
            
            # Clean extracted text
            cleaned_text = self._clean_text(text)
            
            # Extract structured fields
            fields = self._extract_fields(cleaned_text)
            
            return {
                "success": True,
                "text": cleaned_text,
                "confidence": float(confidence) if isinstance(confidence, (int, float)) else 0.0,
                "fields": fields,
                "raw_text": text
            }
        
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "confidence": 0.0
            }
        finally:
            # Cleanup
            try:
                Path(temp_file).unlink()
            except:
                pass
    
    def _preprocess_image(self, image_path: str) -> np.ndarray:
        """Preprocess image for better OCR"""
        if not CV2_AVAILABLE:
            return image_path
        
        # Read image
        img = cv2.imread(image_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
        
        # Save preprocessed
        cv2.imwrite(image_path, denoised)
        
        return image_path
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common OCR errors
        text = text.replace('|', 'I')
        text = text.replace('0', 'O')  # context-dependent
        
        # Remove special characters
        text = re.sub(r'[^\w\s.,;:!?()-]', '', text)
        
        return text.strip()
    
    def _extract_fields(self, text: str) -> Dict[str, Any]:
        """Extract structured fields from text"""
        fields = {}
        
        # Extract dates
        date_pattern = r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}'
        dates = re.findall(date_pattern, text)
        if dates:
            fields["dates"] = dates
        
        # Extract Aadhaar number (12 digits)
        aadhaar_pattern = r'\b\d{12}\b'
        aadhaar = re.findall(aadhaar_pattern, text)
        if aadhaar:
            fields["aadhaar_numbers"] = aadhaar
        
        # Extract phone numbers
        phone_pattern = r'\b\d{10,}\b'
        phones = re.findall(phone_pattern, text)
        if phones:
            fields["phone_numbers"] = phones[:3]  # Limit to 3
        
        # Extract names (capitalized words)
        name_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
        names = re.findall(name_pattern, text)
        if names:
            fields["potential_names"] = names[:5]
        
        # Extract email
        email_pattern = r'\b[\w.-]+@[\w.-]+\.\w+\b'
        emails = re.findall(email_pattern, text)
        if emails:
            fields["emails"] = emails
        
        # Extract PIN codes (6 digits)
        pin_pattern = r'\b\d{6}\b'
        pins = re.findall(pin_pattern, text)
        if pins:
            fields["pin_codes"] = pins
        
        return fields


# Singleton instance
ocr_service = OCRService()



