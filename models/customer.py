from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Customer:
    id: Optional[int] = None
    company_id: int = 0
    name: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    gst_no: str = ""
    created_at: Optional[datetime] = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'gst_no': self.gst_no,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get('id'),
            company_id=data.get('company_id', 0),
            name=data.get('name', ''),
            phone=data.get('phone', ''),
            email=data.get('email', ''),
            address=data.get('address', ''),
            gst_no=data.get('gst_no', ''),
            created_at=data.get('created_at')
        )
    
    def validate(self) -> list:
        errors = []
        if not self.name.strip():
            errors.append("Customer name is required")
        if self.company_id <= 0:
            errors.append("Valid company selection is required")
        if self.email and '@' not in self.email:
            errors.append("Invalid email format")
        if self.phone and len(self.phone.replace(' ', '').replace('-', '')) < 10:
            errors.append("Phone number should be at least 10 digits")
        return errors
