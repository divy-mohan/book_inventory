from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Company:
    id: Optional[int] = None
    name: str = ""
    registration_no: str = ""
    address: str = ""
    phone: str = ""
    email: str = ""
    gst_no: str = ""
    created_at: Optional[datetime] = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'registration_no': self.registration_no,
            'address': self.address,
            'phone': self.phone,
            'email': self.email,
            'gst_no': self.gst_no,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            registration_no=data.get('registration_no', ''),
            address=data.get('address', ''),
            phone=data.get('phone', ''),
            email=data.get('email', ''),
            gst_no=data.get('gst_no', ''),
            created_at=data.get('created_at')
        )
    
    def validate(self) -> list:
        errors = []
        if not self.name.strip():
            errors.append("Company name is required")
        if self.email and '@' not in self.email:
            errors.append("Invalid email format")
        return errors
