import pandas as pd
import yfinance as yf
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from yfinance import Ticker

from app.config.utils import verify_load_cache
from app.database.models.fii import Fii, FiiFinancialHistory
from app.schema.fii import FiiSchema

general_file = "fii_geral.csv"
active_passive_file = "fii_ativo_passivo.csv"
complement_file = "fii_complemento.csv"


class FiiFetcherService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def fetch(self, ticker: str) -> FiiSchema:
        fii_result = await self.session.execute(
            select(Fii).filter(Fii.ticker == ticker)
        )
        fii: Fii = fii_result.scalar_one()
        history_result = await self.session.execute(
            select(FiiFinancialHistory)
            .filter(FiiFinancialHistory.fii_id == fii.id)
            .order_by(FiiFinancialHistory.reference_date.desc())
            .limit(1)
        )
        fii_history: FiiFinancialHistory = history_result.scalar_one_or_none()

        vpcota = fii_history.book_value_per_share
        dymes = fii_history.monthly_dividend_yield
        divEmReal = dymes * vpcota

        ticker_yf = yf.Ticker(f"{ticker}.SA")
        ticker_info = ticker_yf.info
        preco = ticker_info.get("currentPrice")
        pvp = preco / vpcota

        return FiiSchema(
            ticker=ticker,
            valor_patrimonial_cota=vpcota,
            data_referencia=fii_history.reference_date,
            dy_mes=dymes,
            dividendo_reais=divEmReal,
            pvp=pvp,
            preco=preco,
        )
