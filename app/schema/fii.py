from datetime import date, datetime
from decimal import ROUND_CEILING, Decimal

from pydantic import BaseModel, Field, field_serializer, field_validator


class FiiSchema(BaseModel):
    ticker: str = Field(...)
    valor_patrimonial_cota: float = Field(...)
    data_referencia: date = Field(...)
    dy_mes: float = Field(...)
    dividendo_reais: float = Field(...)
    pvp: float = Field(...)
    preco: float = Field(...)

    @field_serializer(
        "valor_patrimonial_cota", "dy_mes", "dividendo_reais", "pvp", "preco"
    )
    def format_floats(value, info):
        if value is None:
            return None
        return float(f"{value:.2f}")
