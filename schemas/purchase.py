from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class PurchaseCreate(BaseModel):
    user_id: int
    investment_amount: Decimal = Field(..., gt=0)
    purchase_price: Decimal = Field(..., gt=0)
    btc_quantity: Optional[Decimal] = Field(default=None, gt=0)
    purchase_fee: Decimal = Field(default=Decimal("0"), ge=0)
    purchase_fee_percent: Optional[Decimal] = Field(default=None, ge=0)
    investment_includes_fee: bool = True
    purchase_date: Optional[datetime] = None
    note: Optional[str] = None


class PurchaseResponse(BaseModel):
    id: int
    user_id: int
    investment_amount: Decimal
    investment_includes_fee: bool
    purchase_price: Decimal
    btc_quantity: Decimal
    remaining_btc_quantity: Decimal
    purchase_fee: Decimal
    purchase_fee_percent: Optional[Decimal]
    purchase_date: datetime
    status: str
    note: Optional[str]

    class Config:
        from_attributes = True

