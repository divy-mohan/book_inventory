from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, date

@dataclass
class PurchaseItem:
    book_id: int
    quantity: int
    price_per_unit: float
    total_price: float

@dataclass
class Purchase:
    id: Optional[int] = None
    company_id: int = 0
    book_id: int = 0
    supplier_name: str = ""
    quantity: int = 0
    price_per_unit: float = 0.0
    total_amount: float = 0.0
    purchase_date: Optional[date] = None
    notes: str = ""
    created_at: Optional[datetime] = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'book_id': self.book_id,
            'supplier_name': self.supplier_name,
            'quantity': self.quantity,
            'price_per_unit': self.price_per_unit,
            'total_amount': self.total_amount,
            'purchase_date': self.purchase_date,
            'notes': self.notes,
            'created_at': self.created_at
        }

@dataclass
class SaleItem:
    book_id: int
    quantity: int
    price_per_unit: float
    total_price: float

@dataclass
class Sale:
    id: Optional[int] = None
    company_id: int = 0
    customer_id: Optional[int] = None
    invoice_no: str = ""
    sale_date: Optional[date] = None
    total_amount: float = 0.0
    discount: float = 0.0
    tax_amount: float = 0.0
    final_amount: float = 0.0
    payment_status: str = "Pending"
    notes: str = ""
    created_at: Optional[datetime] = None
    items: List[SaleItem] = None
    
    def __post_init__(self):
        if self.items is None:
            self.items = []
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'customer_id': self.customer_id,
            'invoice_no': self.invoice_no,
            'sale_date': self.sale_date,
            'total_amount': self.total_amount,
            'discount': self.discount,
            'tax_amount': self.tax_amount,
            'final_amount': self.final_amount,
            'payment_status': self.payment_status,
            'notes': self.notes,
            'created_at': self.created_at
        }
    
    def calculate_totals(self):
        """Calculate total amounts based on items"""
        self.total_amount = sum(item.total_price for item in self.items)
        self.final_amount = self.total_amount - self.discount + self.tax_amount
    
    def validate(self) -> list:
        errors = []
        if not self.invoice_no.strip():
            errors.append("Invoice number is required")
        if self.company_id <= 0:
            errors.append("Valid company selection is required")
        if not self.items:
            errors.append("At least one item is required")
        if self.discount < 0:
            errors.append("Discount cannot be negative")
        if self.tax_amount < 0:
            errors.append("Tax amount cannot be negative")
        return errors
