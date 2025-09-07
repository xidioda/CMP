"""
Test OCR functionality with the generated sample invoice
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cmp.utils.ocr import ocr_processor

async def test_ocr():
    """Test OCR processing with sample invoice"""
    
    # Test file path
    test_image = Path("/Users/xidioda/Projects/CMP/test_files/sample_invoice.png")
    
    if not test_image.exists():
        print(f"Test image not found: {test_image}")
        return
    
    print(f"Testing OCR with: {test_image}")
    print("=" * 50)
    
    # Test raw text extraction
    print("1. Raw text extraction:")
    raw_text = await ocr_processor.extract_text(test_image)
    print(f"Extracted text ({len(raw_text)} characters):")
    print(raw_text)
    print("\n" + "=" * 50)
    
    # Test structured data extraction
    print("2. Structured invoice data extraction:")
    invoice_data = await ocr_processor.extract_invoice_data(test_image)
    
    for key, value in invoice_data.items():
        if key == "raw_text":
            continue  # Skip raw text (already shown)
        print(f"{key}: {value}")
    
    print("\n" + "=" * 50)
    print("OCR Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_ocr())
