from datetime import datetime

from receipt_processor import db


class ReceiptFile(db.Model):
    __tablename__ = 'receipt_file'
    
    id = db.Column(db.String(36), primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False, unique=True)
    is_valid = db.Column(db.Boolean, default=False)
    invalid_reason = db.Column(db.String(255), nullable=True)
    is_processed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'is_valid': self.is_valid,
            'invalid_reason': self.invalid_reason,
            'is_processed': self.is_processed,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Receipt(db.Model):
    __tablename__ = 'receipt'
    
    id = db.Column(db.String(36), primary_key=True)
    receipt_file_id = db.Column(db.String(36), db.ForeignKey('receipt_file.id'), nullable=False)
    purchased_at = db.Column(db.DateTime, nullable=True)
    merchant_name = db.Column(db.String(255), nullable=True)
    total_amount = db.Column(db.Float, nullable=True)
    file_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional fields for transaction details
    currency = db.Column(db.String(10), nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)
    tax_amount = db.Column(db.Float, nullable=True)
    receipt_number = db.Column(db.String(50), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'receipt_file_id': self.receipt_file_id,
            'purchased_at': self.purchased_at.isoformat() if self.purchased_at else None,
            'merchant_name': self.merchant_name,
            'total_amount': self.total_amount,
            'currency': self.currency,
            'payment_method': self.payment_method,
            'tax_amount': self.tax_amount,
            'receipt_number': self.receipt_number,
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

# Create the items table to store individual receipt items
class ReceiptItem(db.Model):
    __tablename__ = 'receipt_item'
    
    id = db.Column(db.String(36), primary_key=True)
    receipt_id = db.Column(db.String(36), db.ForeignKey('receipt.id'), nullable=False)
    item_name = db.Column(db.String(255), nullable=True)
    quantity = db.Column(db.Float, nullable=True)
    unit_price = db.Column(db.Float, nullable=True)
    total_price = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'receipt_id': self.receipt_id,
            'item_name': self.item_name,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_price': self.total_price,
            'created_at': self.created_at.isoformat()
        }

