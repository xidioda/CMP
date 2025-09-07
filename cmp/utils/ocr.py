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
        """Extract raw text from an image file with enhanced OCR settings"""
        if not TESSERACT_AVAILABLE:
            logger.warning("OCR requested but Tesseract not available")
            return ""
        
        try:
            # Open and process image
            with Image.open(file_path) as image:
                # Convert to RGB if necessary
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Enhanced OCR configuration for better accuracy
                custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz./:-# '
                
                # Extract text using OCR with multiple language support
                text = pytesseract.image_to_string(
                    image, 
                    lang='eng+ara',  # English + Arabic for UAE
                    config=custom_config
                )
                logger.info(f"OCR extracted {len(text)} characters from {file_path.name}")
                return text.strip()
                
        except Exception as e:
            logger.error(f"OCR processing failed for {file_path}: {e}")
            return ""
    
    async def extract_invoice_data(self, file_path: Path) -> Dict[str, Any]:
        """Extract structured invoice data from an image with confidence scoring"""
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
        
        # Extract structured data
        invoice_number = self._extract_invoice_number(text)
        date = self._extract_date(text)
        vendor = self._extract_vendor(text)
        amount = self._extract_amount(text)
        currency = self._extract_currency(text)
        line_items = self._extract_line_items(text)
        
        # Calculate confidence based on extracted data completeness
        confidence = self._calculate_confidence(
            text, invoice_number, date, vendor, amount, line_items
        )
        
        invoice_data = {
            "raw_text": text,
            "invoice_number": invoice_number,
            "date": date,
            "vendor": vendor,
            "amount": amount,
            "currency": currency,
            "line_items": line_items,
            "confidence": confidence
        }
        
        logger.info(f"Extracted invoice data from {file_path.name}: {invoice_data['invoice_number']} (confidence: {confidence:.2f})")
        return invoice_data
    
    def _calculate_confidence(self, text: str, invoice_number: Optional[str], 
                            date: Optional[str], vendor: Optional[str], 
                            amount: Optional[float], line_items: list) -> float:
        """Calculate confidence score based on extracted data completeness"""
        if not TESSERACT_AVAILABLE:
            return 0.0
        
        score = 0.0
        max_score = 1.0
        
        # Text quality (based on length and content)
        if len(text) > 50:
            score += 0.2
        
        # Key fields extraction
        if invoice_number:
            score += 0.2
        if date:
            score += 0.15
        if vendor:
            score += 0.15
        if amount and amount > 0:
            score += 0.2
        
        # Line items quality
        if line_items:
            score += 0.1
            # Bonus for structured items
            structured_items = sum(1 for item in line_items if item.get('quantity') is not None)
            if structured_items > 0:
                score += min(0.1, structured_items * 0.02)
        
        return min(score, max_score)
    
    def _extract_invoice_number(self, text: str) -> Optional[str]:
        """Extract invoice number from text using enhanced patterns"""
        import re
        
        patterns = [
            r'invoice\s*#?:?\s*([A-Z0-9\-]+(?:\-\d{4}\-\d{3})?)',
            r'inv\s*#?:?\s*([A-Z0-9\-]+(?:\-\d{4}\-\d{3})?)',
            r'bill\s*#?:?\s*([A-Z0-9\-]+(?:\-\d{4}\-\d{3})?)',
            r'#\s*([A-Z]{2,}\-\d{4}\-\d{3})',  # Pattern like INV-2024-001
            r'([A-Z]{2,}\-\d{4}\-\d{3})',  # Direct pattern match
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                inv_num = match.group(1).strip()
                # Filter out common false positives
                if inv_num not in ['UAE', 'TRN', 'VAT'] and len(inv_num) >= 3:
                    return inv_num
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
        """Extract total amount from text with enhanced patterns"""
        import re
        
        # Look for total amount patterns
        patterns = [
            r'total[:\s]*([A-Z]{3})?[:\s]*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'amount[:\s]*([A-Z]{3})?[:\s]*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*AED',
            r'total:\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # Simple total: pattern
            r'grand\s*total[:\s]*(\d+(?:,\d{3})*(?:\.\d{2})?)',
        ]
        
        amounts = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    # Handle tuple matches (with currency group)
                    amount_str = match[-1] if isinstance(match, tuple) else match
                    try:
                        amount = float(amount_str.replace(',', ''))
                        amounts.append(amount)
                    except ValueError:
                        continue
        
        # Return the largest amount found (likely the total)
        return max(amounts) if amounts else None
    
    def _extract_currency(self, text: str) -> str:
        """Extract currency from text, default to AED for UAE"""
        import re
        
        currencies = ['AED', 'USD', 'EUR', 'GBP', 'SAR']
        for currency in currencies:
            if re.search(rf'\b{currency}\b', text, re.IGNORECASE):
                return currency
        return "AED"  # Default for UAE
    
    def _extract_line_items(self, text: str) -> list:
        """Extract line items from invoice with enhanced parsing"""
        import re
        
        lines = text.split('\n')
        items = []
        
        # Look for structured item lines with quantity, price, and amount
        item_pattern = r'(.+?)\s+(\d+)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)'
        
        for line in lines:
            line = line.strip()
            
            # Skip headers and non-item lines
            if not line or line.lower().startswith(('description', 'qty', 'price', 'amount', 'total', 'subtotal', 'vat', 'bill to', 'invoice', 'trn:', 'date:', 'payment')):
                continue
            
            # Try structured pattern first
            match = re.match(item_pattern, line)
            if match:
                desc, qty, price, amount = match.groups()
                items.append({
                    "description": desc.strip(),
                    "quantity": int(qty),
                    "unit_price": float(price.replace(',', '')),
                    "amount": float(amount.replace(',', ''))
                })
            # Fallback for lines that look like items but don't match exact pattern
            elif re.search(r'\d+', line) and len(line) > 10 and not re.search(r'(AED|Total|VAT)', line, re.IGNORECASE):
                # Extract numbers from the line for potential qty/amounts
                numbers = re.findall(r'[\d,]+\.?\d*', line)
                if len(numbers) >= 2:
                    # Remove numbers from description
                    desc = re.sub(r'[\d,]+\.?\d*', '', line).strip()
                    items.append({
                        "description": desc,
                        "quantity": None,
                        "unit_price": None,
                        "amount": None
                    })
        
        return items[:10]  # Limit to first 10 items


# Global OCR processor instance
ocr_processor = OCRProcessor()
