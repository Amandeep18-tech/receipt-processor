import uuid

from flask import current_app
from werkzeug.utils import secure_filename
import pdf2image
import pytesseract
import re
import PyPDF2
from dateutil import parser as date_parser
from receipt_processor.nlp.spacy_model import nlp

def is_valid_pdf(file_path):
    """Check if a file is a valid PDF."""
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            if len(reader.pages) > 0:
                return True, None
            else:
                return False, "PDF has no pages"
    except Exception as e:
        return False, str(e)

def generate_unique_filename(original_filename):
    """Generate a unique filename to avoid overwrites."""
    filename = secure_filename(original_filename)
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    return unique_filename

def extract_text_from_pdf(file_path):
    """Extract text from PDF using OCR."""
    try:
        # Convert PDF to images
        print('here')
        images = pdf2image.convert_from_path(file_path)

        # Extract text from each image
        extracted_text = ""
        for image in images:
            
            text = pytesseract.image_to_string(image)
            extracted_text += text + "\n"
        
        return extracted_text
    except Exception as e:
        current_app.logger.error(f"Error extracting text from PDF: {str(e)}")
        return None

def parse_receipt_text(text):
    """
    Parse extracted text to find receipt details using regex patterns and NLP.
    Returns a dictionary with the extracted information.
    """
    if not text:
        return {}
    
    # Initialize result dictionary
    result = {
        'merchant_name': None,
        'purchased_at': None,
        'total_amount': None,
        'currency': None,
        'payment_method': None,
        'tax_amount': None,
        'receipt_number': None,
        'items': []
    }
    
    # Process text with spaCy for named entity recognition
    doc = nlp(text)
    
    # Extract merchant name (usually at the top of the receipt)
    merchant_lines = text.strip().split('\n')[:3]  # Consider first 3 lines for merchant name
    for line in merchant_lines:
        line = line.strip()
        if line and len(line) > 3 and not line.startswith('http') and not re.search(r'\d{2}/\d{2}/\d{4}', line):
            result['merchant_name'] = line
            break
    
    # Extract date using regex patterns
    date_patterns = [
        r'\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY
        r'\d{2}-\d{2}-\d{4}',  # DD-MM-YYYY
        r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
        r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
        r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}',  # DD Month YYYY
    ]
    
    for pattern in date_patterns:
        date_match = re.search(pattern, text)
        if date_match:
            try:
                result['purchased_at'] = date_parser.parse(date_match.group(0))
                break
            except:
                continue
    
    # Extract total amount
    total_patterns = [
        r'(?:total|amount|sum|balance).{0,20}(?:[$€£¥]|\d)\s*[\d,.]+',
        r'(?:[$€£¥]|\d)\s*[\d,.]+\s*(?:total|amount)',
        r'total\s*(?:[$€£¥]|\d)\s*[\d,.]+',
    ]
    
    for pattern in total_patterns:
        total_match = re.search(pattern, text, re.IGNORECASE)
        if total_match:
            amount_str = re.search(r'(?:[$€£¥]|\d)\s*[\d,.]+', total_match.group(0))
            if amount_str:
                # Clean the amount string
                amount_text = amount_str.group(0).replace(',', '.')
                # Extract numeric part
                numeric_part = re.search(r'[\d.]+', amount_text)
                if numeric_part:
                    result['total_amount'] = float(numeric_part.group(0))
                    # Check for currency
                    currency_match = re.search(r'[$€£¥]', amount_text)
                    if currency_match:
                        currency_map = {
                            '$': 'USD',
                            '€': 'EUR',
                            '£': 'GBP',
                            '¥': 'JPY'
                        }
                        result['currency'] = currency_map.get(currency_match.group(0), 'USD')
                    break
    
    # Extract payment method
    payment_patterns = [
        r'(?:paid|payment|method).{0,15}(?:cash|credit|debit|visa|mastercard|amex|paypal)',
        r'(?:cash|credit|debit|visa|mastercard|amex|paypal)',
    ]
    
    for pattern in payment_patterns:
        payment_match = re.search(pattern, text, re.IGNORECASE)
        if payment_match:
            payment_text = payment_match.group(0).lower()
            if 'cash' in payment_text:
                result['payment_method'] = 'Cash'
            elif 'credit' in payment_text or 'visa' in payment_text or 'mastercard' in payment_text or 'amex' in payment_text:
                result['payment_method'] = 'Credit Card'
            elif 'debit' in payment_text:
                result['payment_method'] = 'Debit Card'
            elif 'paypal' in payment_text:
                result['payment_method'] = 'PayPal'
            break
    
    # Extract tax amount
    tax_patterns = [
        r'(?:tax|vat|gst).{0,15}(?:[$€£¥]|\d)\s*[\d,.]+',
        r'(?:[$€£¥]|\d)\s*[\d,.]+\s*(?:tax|vat|gst)',
    ]
    
    for pattern in tax_patterns:
        tax_match = re.search(pattern, text, re.IGNORECASE)
        if tax_match:
            tax_str = re.search(r'(?:[$€£¥]|\d)\s*[\d,.]+', tax_match.group(0))
            if tax_str:
                # Clean the tax amount string
                tax_text = tax_str.group(0).replace(',', '.')
                # Extract numeric part
                numeric_part = re.search(r'[\d.]+', tax_text)
                if numeric_part:
                    result['tax_amount'] = float(numeric_part.group(0))
                    break
    
    # Extract receipt number
    receipt_patterns = [
        r'(?:receipt|invoice|order|transaction).{0,5}(?:#|no|num|number).{0,5}[\w\d-]+',
        r'(?:#|no|num|number).{0,5}[\w\d-]+',
    ]
    
    for pattern in receipt_patterns:
        receipt_match = re.search(pattern, text, re.IGNORECASE)
        if receipt_match:
            receipt_text = receipt_match.group(0)
            number_part = re.search(r'[\w\d-]+$', receipt_text)
            if number_part:
                result['receipt_number'] = number_part.group(0)
                break
    
    # Try to extract item lines (this is very challenging and might need refinement)
    # Look for patterns like "1 x Item $10.99" or "Item............$10.99"
    item_patterns = [
        r'(\d+)?\s*[xX]?\s*([a-zA-Z\s]+)[-\s.]*(\$?\d+\.\d{2})',
        r'([a-zA-Z\s]+)[-\s.]*(\$?\d+\.\d{2})',
    ]
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if len(line) > 5:  # Ignore very short lines
            for pattern in item_patterns:
                item_match = re.search(pattern, line)
                if item_match:
                    groups = item_match.groups()
                    
                    if len(groups) == 3:  # Pattern with quantity
                        quantity = float(groups[0]) if groups[0] else 1
                        item_name = groups[1].strip()
                        price_str = groups[2].replace('$', '').strip()
                        try:
                            price = float(price_str)
                            result['items'].append({
                                'item_name': item_name,
                                'quantity': quantity,
                                'unit_price': price / quantity,
                                'total_price': price
                            })
                        except ValueError:
                            pass
                    elif len(groups) == 2:  # Pattern without quantity
                        item_name = groups[0].strip()
                        price_str = groups[1].replace('$', '').strip()
                        try:
                            price = float(price_str)
                            result['items'].append({
                                'item_name': item_name,
                                'quantity': 1,
                                'unit_price': price,
                                'total_price': price
                            })
                        except ValueError:
                            pass
    
    return result
