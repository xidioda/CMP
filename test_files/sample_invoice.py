"""
Generate a sample invoice image for testing OCR functionality
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_sample_invoice():
    """Create a sample invoice image for OCR testing"""
    
    # Create a white image
    width, height = 800, 1000
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Try to use a system font, fallback to default
    try:
        # macOS system font
        font_large = ImageFont.truetype('/System/Library/Fonts/Arial.ttf', 24)
        font_medium = ImageFont.truetype('/System/Library/Fonts/Arial.ttf', 18)
        font_small = ImageFont.truetype('/System/Library/Fonts/Arial.ttf', 14)
    except:
        # Fallback to default font
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    y_pos = 50
    
    # Company header
    draw.text((50, y_pos), "AL MANARA TRADING LLC", fill='black', font=font_large)
    y_pos += 40
    draw.text((50, y_pos), "Dubai, UAE", fill='black', font=font_medium)
    y_pos += 30
    draw.text((50, y_pos), "TRN: 123456789000003", fill='black', font=font_small)
    y_pos += 50
    
    # Invoice header
    draw.text((50, y_pos), "INVOICE", fill='black', font=font_large)
    draw.text((500, y_pos), "Invoice #: INV-2024-001", fill='black', font=font_medium)
    y_pos += 40
    draw.text((500, y_pos), "Date: 15/01/2024", fill='black', font=font_medium)
    y_pos += 50
    
    # Bill to
    draw.text((50, y_pos), "Bill To:", fill='black', font=font_medium)
    y_pos += 30
    draw.text((50, y_pos), "ABC COMPANY", fill='black', font=font_small)
    y_pos += 25
    draw.text((50, y_pos), "Business Bay, Dubai", fill='black', font=font_small)
    y_pos += 25
    draw.text((50, y_pos), "TRN: 987654321000001", fill='black', font=font_small)
    y_pos += 50
    
    # Items table header
    draw.text((50, y_pos), "Description", fill='black', font=font_medium)
    draw.text((400, y_pos), "Qty", fill='black', font=font_medium)
    draw.text((500, y_pos), "Price", fill='black', font=font_medium)
    draw.text((600, y_pos), "Amount", fill='black', font=font_medium)
    y_pos += 30
    
    # Draw line
    draw.line([(50, y_pos), (700, y_pos)], fill='black', width=2)
    y_pos += 20
    
    # Items
    items = [
        ("Office Supplies", "10", "25.00", "250.00"),
        ("Computer Equipment", "2", "1,500.00", "3,000.00"),
        ("Software License", "1", "500.00", "500.00"),
    ]
    
    for desc, qty, price, amount in items:
        draw.text((50, y_pos), desc, fill='black', font=font_small)
        draw.text((400, y_pos), qty, fill='black', font=font_small)
        draw.text((500, y_pos), price, fill='black', font=font_small)
        draw.text((600, y_pos), amount, fill='black', font=font_small)
        y_pos += 25
    
    y_pos += 30
    draw.line([(450, y_pos), (700, y_pos)], fill='black', width=1)
    y_pos += 20
    
    # Totals
    draw.text((450, y_pos), "Subtotal:", fill='black', font=font_medium)
    draw.text((600, y_pos), "3,750.00 AED", fill='black', font=font_medium)
    y_pos += 30
    
    draw.text((450, y_pos), "VAT (5%):", fill='black', font=font_medium)
    draw.text((600, y_pos), "187.50 AED", fill='black', font=font_medium)
    y_pos += 30
    
    draw.text((450, y_pos), "Total:", fill='black', font=font_large)
    draw.text((600, y_pos), "3,937.50 AED", fill='black', font=font_large)
    y_pos += 50
    
    # Payment terms
    draw.text((50, y_pos), "Payment Terms: Net 30 days", fill='black', font=font_small)
    y_pos += 25
    draw.text((50, y_pos), "Thank you for your business!", fill='black', font=font_small)
    
    # Save the image
    output_path = '/Users/xidioda/Projects/CMP/test_files/sample_invoice.png'
    image.save(output_path)
    print(f"Sample invoice saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    create_sample_invoice()
