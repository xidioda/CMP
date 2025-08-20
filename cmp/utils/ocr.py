"""
OCR Processing Module

Handles optical character recognition for invoices and receipts using pytesseract.
Includes fallback handling if Tesseract is not installed.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
import tempfile
import shutil

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

from ..logging_config import get_logger

logger = get_logger("ocr")


class OCRProcessor:
    """OCR processor for extracting text from invoice and receipt images"""
    
    def __init__(self):
        self.supported_formats = {".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".pdf"}
        
        if not TESSERACT_AVAILABLE:
            logger.warning(
                "Tesseract/pytesseract not available. OCR functionality will be limited. "
                "Install with: brew install tesseract && pip install pytesseract"
            )
    
    async def extract_text(self, file_path: Path) -> str:
        """Extract raw text from an image file"""
        if not TESSERACT_AVAILABLE:
            logger.warning("OCR requested but Tesseract not available")
            return ""
        
        try:
            # Open and process image
            with Image.open(file_path) as image:
                # Convert to RGB if necessary
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Extract text using OCR
                text = pytesseract.image_to_string(image, lang='eng+ara')  # English + Arabic for UAE
                logger.info(f"OCR extracted {len(text)} characters from {file_path.name}")
                return text.strip()
                
        except Exception as e:
            logger.error(f"OCR processing failed for {file_path}: {e}")
            return ""
    
    async def extract_invoice_data(self, file_path: Path) -> Dict[str, Any]:
        """Extract structured invoice data from an image"""
        text = await self.extract_text(file_path)
        
        if not text:
            return {
                "raw_text": "",
                "invoice_number": None,
                "date": None,
                "vendor": None,
                "amount": None,
                "currency": "AED",
                "line_items": [],
                "confidence": 0.0
            }
        
        # Basic text parsing (this would be enhanced with ML/NLP in production)
        invoice_data = {
            "raw_text": text,
            "invoice_number": self._extract_invoice_number(text),
            "date": self._extract_date(text),
            "vendor": self._extract_vendor(text),
            "amount": self._extract_amount(text),
            "currency": self._extract_currency(text),
            "line_items": self._extract_line_items(text),
            "confidence": 0.7 if TESSERACT_AVAILABLE else 0.0  # Placeholder confidence
        }
        
        logger.info(f"Extracted invoice data from {file_path.name}: {invoice_data['invoice_number']}")
        return invoice_data
    
    def _extract_invoice_number(self, text: str) -> Optional[str]:
        """Extract invoice number from text using basic patterns"""
        import re
        
        patterns = [
            r'invoice\s*#?\s*([A-Z0-9\-]+)',
            r'inv\s*#?\s*([A-Z0-9\-]+)',
            r'bill\s*#?\s*([A-Z0-9\-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from text using basic patterns"""
        import re
        
        # Common date patterns
        patterns = [
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
            r'\b(\d{2,4}[/-]\d{1,2}[/-]\d{1,2})\b',
            r'\b(\w+ \d{1,2}, \d{4})\b',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_vendor(self, text: str) -> Optional[str]:
        """Extract vendor name from text (first few lines typically)"""
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if len(line) > 3 and not line.isdigit():
                return line
        return None
    
    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract total amount from text"""
        import re
        
        # Look for total amount patterns
        patterns = [
            r'total[:\s]*([A-Z]{3})?[:\s]*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'amount[:\s]*([A-Z]{3})?[:\s]*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*AED',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Get the last match (usually the total)
                amount_str = matches[-1][-1] if isinstance(matches[-1], tuple) else matches[-1]
                try:
                    return float(amount_str.replace(',', ''))
                except ValueError:
                    continue
        return None
    
    def _extract_currency(self, text: str) -> str:
        """Extract currency from text, default to AED for UAE"""
        import re
        
        currencies = ['AED', 'USD', 'EUR', 'GBP', 'SAR']
        for currency in currencies:
            if re.search(rf'\b{currency}\b', text, re.IGNORECASE):
                return currency
        return "AED"  # Default for UAE
    
    def _extract_line_items(self, text: str) -> list:
        """Extract line items from invoice (basic implementation)"""
        import re
        
        # This would be enhanced with more sophisticated parsing
        lines = text.split('\n')
        items = []
        
        for line in lines:
            # Look for lines that might be items (contain numbers and text)
            if re.search(r'\d+', line) and len(line.strip()) > 10:
                items.append({
                    "description": line.strip(),
                    "amount": None,  # Would extract from line
                    "quantity": None
                })
        
        return items[:10]  # Limit to first 10 potential items


# Global OCR processor instance
ocr_processor = OCRProcessor()
