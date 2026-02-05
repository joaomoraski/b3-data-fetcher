import uuid
from datetime import datetime

from sqlalchemy import (
    UUID,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    desc,
)
from sqlalchemy.orm import relationship

from app.database.base import BaseModel
from app.schema.fii import FiiFinancialHistory


class Fii(BaseModel):
    __tablename__ = "fiis"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    cnpj = Column(String, unique=True, nullable=False, index=True)
    ticker = Column(String, unique=True, nullable=True, index=True)
    name = Column(String)
    segment = Column(String)
    management_type = Column(String)
    administrator = Column(String)
    target_audience = Column(String)
    start_date = Column(Date)
    website = Column(String)
    isin_code = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    financial_history = relationship(
        "FiiFinancialHistory",
        back_populates="fii",
        lazy="selectin",
        order_by=desc("reference_date"),
    )


class FiiFinancialHistory(BaseModel):
    __tablename__ = "fii_financial_history"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    fii_id = Column(UUID, ForeignKey("fiis.id", ondelete="CASCADE"), nullable=False)
    reference_date = Column(Date, index=True, nullable=False)
    net_worth = Column(Float)
    issued_shares = Column(Float)
    book_value_per_share = Column(Float)
    monthly_dividend_yield = Column(Float)
    monthly_equity_return = Column(Float)
    monthly_effective_return = Column(Float)
    amortization_per_share = Column(Float)
    total_investors = Column(Float)
    total_liabilities = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    fii = relationship("Fii", back_populates="financial_history")

    __table_args__ = (
        UniqueConstraint("fii_id", "reference_date", name="_fii_date_uc"),
    )
