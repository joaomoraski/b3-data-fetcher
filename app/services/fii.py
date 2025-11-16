from typing import Any, Coroutine

import numpy as np
import pandas as pd
import yfinance as yf
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from yfinance import Ticker, Tickers

from app.adapter.fii import (
    fii_in_to_out_financial_history,
    fii_in_to_out_general,
    fii_in_to_out_general_history,
    fii_in_to_out_general_price,
    fii_ranking_to_out,
)
from app.config.utils import verify_load_cache
from app.database.models.fii import Fii, FiiFinancialHistory
from app.database.repositories.repositories import FiiRepository
from app.schema.fii import (
    FiiDyPvpVol,
    FiiGeneral,
    FiiGeneralHistory,
    FiiGeneralPrice,
    FiiSummary,
)

general_file = "fii_geral.csv"
active_passive_file = "fii_ativo_passivo.csv"
complement_file = "fii_complemento.csv"


class FiiService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = FiiRepository(session)

    async def tcc(self, ticker: str) -> FiiDyPvpVol:
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

        # Baixa 1 ano de histórico
        # investigar o que o auto_adjust faz
        df = yf.download(f"{ticker}.SA", period="1y", interval="1d", auto_adjust=True)
        preco = df["Close"].iloc[-1]
        pvp = preco / vpcota

        # Usa o preço de fechamento ajustado
        fechamento = df["Close"]

        # Calcula retornos diários (percentuais)
        retornos = fechamento.pct_change().dropna()

        # Calcula volatilidade anualizada
        vol_anual = np.std(retornos, axis=0) * np.sqrt(252)

        return FiiDyPvpVol(
            ticker=ticker,
            valor_patrimonial_cota=vpcota,
            data_referencia=fii_history.reference_date,
            dy_mes=dymes,
            dividendo_reais=divEmReal,
            pvp=pvp,
            preco=preco,
            vol_anual=vol_anual,
        )

    async def count(self):
        return await self.repo.count()

    async def list(self, limit: int, offset: int) -> list[FiiGeneral]:
        fiis: list[Fii] = await self.repo.get_list(
            params={"ticker_not_null": True, "limit": limit, "offset": offset}
        )

        return [fii_in_to_out_general(fii) for fii in fiis]

    async def get_one(self, ticker: str) -> FiiGeneralPrice:
        fii: Fii = await self.repo.get_by_field(f"ticker:{ticker}")

        ticker = yf.Ticker(f"{ticker}.SA")

        return fii_in_to_out_general_price(fii, ticker.info.get("currentPrice"))

    async def ticker_history(self, ticker: str) -> FiiGeneralHistory:
        fii: Fii = await self.repo.get_by_field(f"ticker:{ticker}")

        ticker = yf.Ticker(f"{ticker}.SA")

        price = ticker.info.get("currentPrice")

        fii_history = [
            fii_in_to_out_financial_history(history, price)
            for history in fii.financial_history
        ]

        return fii_in_to_out_general_history(fii, fii_history, price)

    async def ticker_history_latest(self, ticker: str) -> FiiGeneralHistory:
        fii: Fii = await self.repo.get_by_field(f"ticker:{ticker}")

        ticker = yf.Ticker(f"{ticker}.SA")

        price = ticker.info.get("currentPrice")

        fii_history = [fii_in_to_out_financial_history(fii.financial_history[0], price)]

        return fii_in_to_out_general_history(fii, fii_history, price)

    async def ticker_summary(self, ticker_name: str) -> FiiSummary:
        fii: Fii = await self.repo.get_by_field(f"ticker:{ticker_name}")
        ticker = yf.Ticker(f"{ticker_name}.SA")
        price = ticker.info.get("currentPrice")

        latest_financial_history: FiiFinancialHistory = fii.financial_history[0]

        pvp = price / latest_financial_history.book_value_per_share
        monthly_dividend_yield = latest_financial_history.monthly_dividend_yield
        real_monthly_dy = (
            latest_financial_history.monthly_dividend_yield
            * latest_financial_history.book_value_per_share
        )
        df = yf.download(
            f"{ticker_name}.SA", period="1y", interval="1d", auto_adjust=True
        )
        # Usa o preço de fechamento ajustado
        closing = df["Close"]
        # Calcula retornos diários (percentuais)
        returns = closing.pct_change().dropna()
        # Calcula volatilidade mensal, trimestral, anual
        vol_dict = {
            "month_vol": np.std(returns, axis=0) * np.sqrt(23),
            "quarter_vol": np.std(returns, axis=0) * np.sqrt(65),
            "annual_vol": np.std(returns, axis=0) * np.sqrt(252),
        }

        number_of_shareholders = latest_financial_history.total_investors
        net_worth = latest_financial_history.net_worth
        last_month_return = latest_financial_history.monthly_effective_return

        # get last year returns
        last_12 = [h.monthly_effective_return for h in fii.financial_history[:12]]
        # fix None occurrences
        last_12 = [x for x in last_12 if x is not None]
        annual_return = float(
            np.prod([1 + x for x in last_12]) - 1 if last_12 else None
        )

        return FiiSummary(
            pvp=pvp,
            monthly_dividend_yield=monthly_dividend_yield,
            volatility=vol_dict,
            number_of_shareholders=number_of_shareholders,
            net_worth=net_worth,
            last_month_return=last_month_return,
            last_year_return=annual_return,
            price=price,
        )

    async def ranking_dy(self, limit: int, offset: int):
        fii = await self.repo.ranking_dy(limit, offset)

        return [
            fii_ranking_to_out(
                fii.name,
                fii.ticker,
                fii.book_value_per_share,
                fii.monthly_dividend_yield,
                fii.monthly_dividend_yield * fii.book_value_per_share,
                fii.reference_date,
            )
            for fii in fii
        ]
