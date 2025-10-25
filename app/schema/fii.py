from decimal import ROUND_CEILING, Decimal

from pydantic import BaseModel, Field, field_validator


class AtivoSchema(BaseModel):
    ticker: str = Field(...)
    valor_patrimonial_cota: float = Field(...)
    dy_mes: float = Field(...)
    dividendo_reais: float = Field(...)
    pvp: float = Field(...)
    preco: float = Field(...)

    @field_validator(
        "valor_patrimonial_cota",
        "dy_mes",
        "dividendo_reais",
        "pvp",
        "preco",
        mode="before",
    )
    def round_two(cls, v):
        if v is None:
            return v
        try:
            valor = Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_CEILING)
            return float(valor)
        except Exception:
            return v
