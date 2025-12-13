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


class FiiGeneralHistory(FiiGeneralPrice):
    history: list["FiiFinancialHistory"] = Field(...)


class FiiSummary(BaseModel):
    pvp: float = Field(...)
    monthly_dividend_yield: float = Field(...)
    volatility: dict[str, float] = Field(...)
    number_of_shareholders: float = Field(...)
    net_worth: float = Field(...)
    last_month_return: float = Field(...)
    last_year_return: float = Field(...)
    price: float = Field(...)


class FiiFinancialHistory(BaseModel):
    reference_date: date = Field(...)
    book_value_per_share: float = Field(...)
    net_worth: float = Field(...)
    monthly_dy: float = Field(...)
    real_monthly_dy: float = Field(...)
    effective_return: float = Field(...)
    number_of_shareholders: float = Field(...)
    liabilities: float = Field(...)


class RankingDy(BaseModel):
    name: str = Field(...)
    ticker: str = Field(...)
    book_value_per_share: float = Field(...)
    dividend_yield: float = Field(...)
    real_dividend_yield: float = Field(...)
    reference_date: date = Field(...)


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
        return float(f"{value:.4f}")


class FiiTccScoreResult(BaseModel):
    ticker: str = Field(..., description="FII ticker")
    dy_normalizado: float = Field(..., description="DY (normalizado)")
    pvp_normalizado: float = Field(..., description="P/VP (normalizado)")
    volatilidade_normalizado: float = Field(
        ..., description="Volatilidade (normalizado)"
    )
    preco: float = Field(..., description="Preço (R$)")
    penalidade_slot: float = Field(..., description="Penalidade Slot")
    score: float = Field(..., description="Score final")


class TccPreliminarSummary(BaseModel):
    total_preco: float = Field(..., description="Preço total dos selecionados")
    orcamento: float = Field(..., description="Orçamento total")
    limite_por_ativo: float = Field(..., description="Limite por ativo (slot)")
    status: str = Field(..., description="Status do orçamento")
    top_k_tickers: list[str] = Field(
        ..., description="Lista dos top K tickers selecionados"
    )


class TccPreliminarResults(BaseModel):
    all_results: list[FiiTccScoreResult] = Field(
        ..., description="Todos os resultados ordenados por score"
    )
    top_k_results: list[FiiTccScoreResult] = Field(
        ..., description="Top K ativos selecionados"
    )
    summary: TccPreliminarSummary = Field(..., description="Resumo da seleção")
