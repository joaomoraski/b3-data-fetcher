from datetime import date, datetime
from decimal import ROUND_CEILING, Decimal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
)


class FiiGeneral(BaseModel):
    cnpj: str = Field(...)
    ticker: str = Field(...)
    name: str = Field(...)
    segment: str = Field(...)
    management_type: str = Field(...)
    administrator: str = Field(...)
    target_audience: str = Field(...)
    start_date: datetime = Field(...)
    website: str = Field(...)
    isin_code: str = Field(...)

    # model_config = ConfigDict(from_attributes=True)


class FiiGeneralPrice(FiiGeneral):
    price: float = Field(...)


class FiiDyPvpVol(BaseModel):
    ticker: str = Field(...)
    valor_patrimonial_cota: float = Field(...)
    data_referencia: date = Field(...)
    dy_mes: float = Field(...)
    dividendo_reais: float = Field(...)
    pvp: float = Field(...)
    preco: float = Field(...)
    vol_anual: float = Field(...)

    @field_serializer(
        "valor_patrimonial_cota",
        "dy_mes",
        "dividendo_reais",
        "pvp",
        "preco",
        "vol_anual",
    )
    def format_floats(value, info):
        if value is None:
            return None
        return float(f"{value:.2f}")
