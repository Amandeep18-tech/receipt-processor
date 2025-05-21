import os
import uuid
from datetime import datetime
from receipt_processor import db
from flask import request, jsonify,Blueprint, current_app
from receipt_processor.models.receipt import Receipt, ReceiptFile, ReceiptItem
from receipt_processor.routes.utils import extract_text_from_pdf, generate_unique_filename, is_valid_pdf, parse_receipt_text

receipt_bp = Blueprint('receipt', __name__)


@receipt_bp.route('/upload', methods=['POST'])
def upload_receipt():
    """Upload a receipt file (PDF only)."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and file.filename.lower().endswith('.pdf'):
        # Generate a unique filename
        filename = generate_unique_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        # Save the file
        file.save(file_path)
        
        # Check if this file has been uploaded before (by comparing content)
        # This is a simplistic approach and might need improvement
        file_hash = hash(open(file_path, 'rb').read())
        
        existing_files = ReceiptFile.query.all()
        for existing_file in existing_files:
            existing_path = existing_file.file_path
            if os.path.exists(existing_path):
                existing_hash = hash(open(existing_path, 'rb').read())
                if existing_hash == file_hash:
                    # Update the existing record
                    existing_file.updated_at = datetime.utcnow()
                    db.session.commit()
                    return jsonify({"message": "File already exists", "receipt_file": existing_file.to_dict()}), 200
        
        # Create a new record
        receipt_file = ReceiptFile(
            id=str(uuid.uuid4()),
            file_name=os.path.basename(file.filename),
            file_path=file_path,
            is_valid=False,
            is_processed=False
        )
        
        db.session.add(receipt_file)
        db.session.commit()
        
        return jsonify({"message": "File uploaded successfully", "receipt_file": receipt_file.to_dict()}), 201
    
    return jsonify({"error": "Invalid file format. Only PDF files are allowed."}), 400

@receipt_bp.route('/validate', methods=['POST'])
def validate_receipt():
    """Validate if the uploaded file is a valid PDF."""
    data = request.json
    
    if not data or 'receipt_file_id' not in data:
        return jsonify({"error": "Missing receipt_file_id parameter"}), 400
    
    receipt_file = ReceiptFile.query.get(data['receipt_file_id'])
    
    if not receipt_file:
        return jsonify({"error": "Receipt file not found"}), 404
    
    if not os.path.exists(receipt_file.file_path):
        receipt_file.is_valid = False
        receipt_file.invalid_reason = "File does not exist"
        db.session.commit()
        return jsonify({"error": "File does not exist", "receipt_file": receipt_file.to_dict()}), 400
    
    is_valid, invalid_reason = is_valid_pdf(receipt_file.file_path)
    
    receipt_file.is_valid = is_valid
    receipt_file.invalid_reason = invalid_reason
    db.session.commit()
    
    return jsonify({
        "message": "File validated",
        "is_valid": is_valid,
        "invalid_reason": invalid_reason,
        "receipt_file": receipt_file.to_dict()
    }), 200

@receipt_bp.route('/process', methods=['POST'])
def process_receipt():
    """Process a receipt file to extract information using OCR."""
    data = request.json
    
    if not data or 'receipt_file_id' not in data:
        return jsonify({"error": "Missing receipt_file_id parameter"}), 400
    
    receipt_file = ReceiptFile.query.get(data['receipt_file_id'])
    
    if not receipt_file:
        return jsonify({"error": "Receipt file not found"}), 404
    
    if not receipt_file.is_valid:
        return jsonify({"error": "Cannot process invalid file", "receipt_file": receipt_file.to_dict()}), 400
    
    if not os.path.exists(receipt_file.file_path):
        return jsonify({"error": "File does not exist", "receipt_file": receipt_file.to_dict()}), 400
    
    # Check if this receipt has already been processed
    existing_receipt = Receipt.query.filter_by(receipt_file_id=receipt_file.id).first()
    if existing_receipt:
        # Update the existing receipt
        receipt_file.is_processed = True
        db.session.commit()
        return jsonify({
            "message": "Receipt already processed",
            "receipt": existing_receipt.to_dict(),
            "receipt_file": receipt_file.to_dict()
        }), 200
    # Extract text from PDF
    extracted_text = extract_text_from_pdf(receipt_file.file_path)
    if not extracted_text:
        return jsonify({"error": "Failed to extract text from PDF"}), 500
    
    # Parse the extracted text
    parsed_data = parse_receipt_text(extracted_text)
    
    # Create a new receipt record
    receipt_id = str(uuid.uuid4())
    receipt = Receipt(
        id=receipt_id,
        receipt_file_id=receipt_file.id,
        purchased_at=parsed_data.get('purchased_at'),
        merchant_name=parsed_data.get('merchant_name'),
        total_amount=parsed_data.get('total_amount'),
        currency=parsed_data.get('currency'),
        payment_method=parsed_data.get('payment_method'),
        tax_amount=parsed_data.get('tax_amount'),
        receipt_number=parsed_data.get('receipt_number'),
        file_path=receipt_file.file_path
    )
    
    db.session.add(receipt)
    
    # Add receipt items if extracted
    for item_data in parsed_data.get('items', []):
        item = ReceiptItem(
            id=str(uuid.uuid4()),
            receipt_id=receipt_id,
            item_name=item_data.get('item_name'),
            quantity=item_data.get('quantity'),
            unit_price=item_data.get('unit_price'),
            total_price=item_data.get('total_price')
        )
        db.session.add(item)
    
    # Mark the receipt file as processed
    receipt_file.is_processed = True
    
    db.session.commit()
    
    # Get the items for the response
    items = [item.to_dict() for item in ReceiptItem.query.filter_by(receipt_id=receipt_id).all()]
    
    receipt_dict = receipt.to_dict()
    receipt_dict['items'] = items
    
    return jsonify({
        "message": "Receipt processed successfully",
        "receipt": receipt_dict,
        "receipt_file": receipt_file.to_dict()
    }), 201

@receipt_bp.route('/receipts', methods=['GET'])
def get_receipts():
    """List all receipts."""
    receipts = Receipt.query.all()
    receipts_with_items = []
    
    for receipt in receipts:
        receipt_dict = receipt.to_dict()
        items = [item.to_dict() for item in ReceiptItem.query.filter_by(receipt_id=receipt.id).all()]
        receipt_dict['items'] = items
        receipts_with_items.append(receipt_dict)
    
    return jsonify({"receipts": receipts_with_items}), 200

@receipt_bp.route('/receipts/<receipt_id>', methods=['GET'])
def get_receipt(receipt_id):
    """Get details of a specific receipt."""
    receipt = Receipt.query.get(receipt_id)
    
    if not receipt:
        return jsonify({"error": "Receipt not found"}), 404
    
    receipt_dict = receipt.to_dict()
    items = [item.to_dict() for item in ReceiptItem.query.filter_by(receipt_id=receipt.id).all()]
    receipt_dict['items'] = items
    
    return jsonify({"receipt": receipt_dict}), 200

@receipt_bp.route('/receipt-files', methods=['GET'])
def get_receipt_files():
    """List all receipt files."""
    receipt_files = ReceiptFile.query.all()
    return jsonify({"receipt_files": [rf.to_dict() for rf in receipt_files]}), 200

@receipt_bp.route('/receipt-files/<receipt_file_id>', methods=['GET'])
def get_receipt_file(receipt_file_id):
    """Get details of a specific receipt file."""
    receipt_file = ReceiptFile.query.get(receipt_file_id)
    
    if not receipt_file:
        return jsonify({"error": "Receipt file not found"}), 404
    
    return jsonify({"receipt_file": receipt_file.to_dict()}), 200