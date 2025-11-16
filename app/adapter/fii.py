from datetime import datetime

from app.database.models.fii import Fii, FiiFinancialHistory
from app.schema.fii import (
    FiiFinancialHistory as FiiFinancialHistorySchema,
)
from app.schema.fii import (
    FiiGeneral,
    FiiGeneralHistory,
    FiiGeneralPrice,
    RankingDy,
)
from app.utils.utils import format_cnpj


def fii_in_to_out_general(fii_in: Fii) -> FiiGeneral:
    return FiiGeneral(
        cnpj=format_cnpj(fii_in.cnpj),
        ticker=fii_in.ticker,
        name=fii_in.name if fii_in.name is not None else fii_in.administrator,
        segment=fii_in.segment,
        management_type=fii_in.management_type,
        administrator=fii_in.administrator,
        target_audience=fii_in.target_audience,
        start_date=datetime(
            fii_in.start_date.year, fii_in.start_date.month, fii_in.start_date.day
        ),
        website=fii_in.website,
        isin_code=fii_in.isin_code,
    )


def fii_in_to_out_general_price(fii_in: Fii, price) -> FiiGeneralPrice:
    base = fii_in_to_out_general(fii_in)
    return FiiGeneralPrice(**base.model_dump(), price=price)


def fii_in_to_out_financial_history(
    fii_financial_in: FiiFinancialHistory, price
) -> FiiFinancialHistorySchema:
    real_monthly_dy = (
        fii_financial_in.monthly_dividend_yield * fii_financial_in.book_value_per_share
    )
    return FiiFinancialHistorySchema(
        reference_date=fii_financial_in.reference_date,
        book_value_per_share=fii_financial_in.book_value_per_share,
        net_worth=fii_financial_in.net_worth,
        monthly_dy=fii_financial_in.monthly_dividend_yield,
        real_monthly_dy=real_monthly_dy,
        effective_return=fii_financial_in.monthly_effective_return,
        number_of_shareholders=fii_financial_in.total_investors,
        liabilities=fii_financial_in.total_liabilities,
    )


def fii_in_to_out_general_history(
    fii_in: Fii, fii_history: list[FiiFinancialHistorySchema], price
) -> FiiGeneralHistory:
    base = fii_in_to_out_general_price(fii_in, price)
    return FiiGeneralHistory(**base.model_dump(), history=fii_history)


def fii_ranking_to_out(
    name,
    ticker,
    book_value_per_share,
    dividend_yield,
    real_dividend_yield,
    reference_date,
) -> RankingDy:
    return RankingDy(
        name=name,
        ticker=ticker,
        book_value_per_share=book_value_per_share,
        dividend_yield=dividend_yield,
        real_dividend_yield=real_dividend_yield,
        reference_date=reference_date,
    )
