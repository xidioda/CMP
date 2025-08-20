import pytest
from pathlib import Path
import tempfile

from cmp.utils.ocr import OCRProcessor


@pytest.fixture
def ocr_processor():
    """Create OCR processor instance for testing"""
    return OCRProcessor()


def test_ocr_processor_initialization(ocr_processor):
    """Test OCR processor initializes correctly"""
    assert ocr_processor is not None
    assert ocr_processor.supported_formats == {".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".pdf"}


@pytest.mark.asyncio
async def test_extract_text_without_tesseract(ocr_processor):
    """Test OCR extraction gracefully handles missing Tesseract"""
    # Create a temporary image file
    with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_file:
        temp_path = Path(temp_file.name)
        
        # This should return empty string if Tesseract not available, no crash
        result = await ocr_processor.extract_text(temp_path)
        assert isinstance(result, str)


@pytest.mark.asyncio 
async def test_extract_invoice_data_structure(ocr_processor):
    """Test invoice data extraction returns proper structure"""
    with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_file:
        temp_path = Path(temp_file.name)
        
        result = await ocr_processor.extract_invoice_data(temp_path)
        
        # Check required fields are present
        required_fields = [
            "raw_text", "invoice_number", "date", "vendor", 
            "amount", "currency", "line_items", "confidence"
        ]
        for field in required_fields:
            assert field in result
        
        # Check types
        assert isinstance(result["raw_text"], str)
        assert isinstance(result["currency"], str)
        assert isinstance(result["line_items"], list)
        assert isinstance(result["confidence"], (int, float))


def test_text_parsing_methods(ocr_processor):
    """Test text parsing helper methods"""
    # Test invoice number extraction
    text_with_invoice = "Invoice #INV-2024-001 for services"
    invoice_num = ocr_processor._extract_invoice_number(text_with_invoice)
    assert invoice_num == "INV-2024-001"
    
    # Test amount extraction  
    text_with_amount = "Total: AED 1,500.00"
    amount = ocr_processor._extract_amount(text_with_amount)
    assert amount == 1500.00
    
    # Test currency extraction
    text_with_currency = "Amount: 500 USD"
    currency = ocr_processor._extract_currency(text_with_currency)
    assert currency == "USD"
    
    # Test default currency (UAE)
    text_no_currency = "Total: 100.00"
    currency = ocr_processor._extract_currency(text_no_currency)
    assert currency == "AED"
