from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class SaleCreate(BaseModel):
    user_id: int
    purchase_id: Optional[int] = None
    btc_quantity_sold: Decimal = Field(..., gt=0)
    sale_price: Decimal = Field(..., gt=0)
    selling_fee: Decimal = Field(default=Decimal("0"), ge=0)
    selling_fee_percent: Optional[Decimal] = Field(default=None, ge=0)
    sold_at: Optional[datetime] = None
    note: Optional[str] = None


class SaleResponse(BaseModel):
    id: int
    user_id: int
    purchase_id: Optional[int]
    btc_quantity_sold: Decimal
    sale_price: Decimal
    gross_sale_amount: Decimal
    selling_fee: Decimal
    net_sale_proceeds: Decimal
    allocated_cost_basis: Decimal
    gross_profit_loss: Decimal
    net_profit_loss: Decimal
    sold_at: datetime
    note: Optional[str]

    class Config:
        from_attributes = True

