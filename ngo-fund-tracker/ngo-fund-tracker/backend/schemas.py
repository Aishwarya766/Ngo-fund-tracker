from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

DonationType = Literal["general", "education", "medical", "food", "other"]


class DonorCreate(BaseModel):
    name: str = Field(min_length=1)
    email: Optional[str] = None
    phone: Optional[str] = None

    @field_validator("email")
    @classmethod
    def _basic_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v


class DonorOut(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime
    total_donations: float = 0.0


class DonationCreate(BaseModel):
    donor_id: int
    amount: float = Field(ge=0)
    type: DonationType
    notes: Optional[str] = None
    date: Optional[datetime] = None


class DonationOut(BaseModel):
    id: int
    donor_id: int
    donor_name: str
    amount: float
    donation_type: DonationType
    date: datetime
    notes: Optional[str] = None


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1)
    description: Optional[str] = None
    allocated_budget: float = Field(ge=0)


class ProjectOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    allocated_budget: float
    created_at: datetime
    total_spent: float = 0.0
    remaining_budget: float = 0.0


class ExpenseCreate(BaseModel):
    project_id: int
    amount: float = Field(ge=0)
    description: str = Field(min_length=1)
    date: Optional[datetime] = None


class ExpenseOut(BaseModel):
    id: int
    project_id: int
    project_name: str
    amount: float
    description: str
    date: datetime


class DashboardOut(BaseModel):
    total_donations: float
    total_expenses: float
    remaining_balance: float
    total_donors: int
