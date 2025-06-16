from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Book:
    id: Optional[int] = None
    company_id: int = 0
    name: str = ""
    author: str = ""
    category: str = ""
    language: str = "English"
    isbn: str = ""
    purchase_price: float = 0.0
    selling_price: float = 0.0
    stock_quantity: int = 0
    damaged_quantity: int = 0
    lost_quantity: int = 0
    created_at: Optional[datetime] = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'name': self.name,
            'author': self.author,
            'category': self.category,
            'language': self.language,
            'isbn': self.isbn,
            'purchase_price': self.purchase_price,
            'selling_price': self.selling_price,
            'stock_quantity': self.stock_quantity,
            'damaged_quantity': self.damaged_quantity,
            'lost_quantity': self.lost_quantity,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get('id'),
            company_id=data.get('company_id', 0),
            name=data.get('name', ''),
            author=data.get('author', ''),
            category=data.get('category', ''),
            language=data.get('language', 'English'),
            isbn=data.get('isbn', ''),
            purchase_price=float(data.get('purchase_price', 0)),
            selling_price=float(data.get('selling_price', 0)),
            stock_quantity=int(data.get('stock_quantity', 0)),
            damaged_quantity=int(data.get('damaged_quantity', 0)),
            lost_quantity=int(data.get('lost_quantity', 0)),
            created_at=data.get('created_at')
        )
    
    def validate(self) -> list:
        errors = []
        if not self.name.strip():
            errors.append("Book name is required")
        if self.company_id <= 0:
            errors.append("Valid company selection is required")
        if self.purchase_price < 0:
            errors.append("Purchase price cannot be negative")
        if self.selling_price < 0:
            errors.append("Selling price cannot be negative")
        if self.stock_quantity < 0:
            errors.append("Stock quantity cannot be negative")
        return errors
    
    @property
    def available_stock(self) -> int:
        return self.stock_quantity - self.damaged_quantity - self.lost_quantity
    
    @property
    def total_value(self) -> float:
        return self.available_stock * self.selling_price
    
    @property
    def profit_per_unit(self) -> float:
        return self.selling_price - self.purchase_price
