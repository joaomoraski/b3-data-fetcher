from typing import Any, Coroutine

import numpy as np
import pandas as pd
import yfinance as yf
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from yfinance import Ticker, Tickers

from app.adapter.fii import fii_in_to_out_general, fii_in_to_out_general_price
from app.config.utils import verify_load_cache
from app.database.models.fii import Fii, FiiFinancialHistory
from app.database.repositories.repositories import FiiRepository
from app.schema.fii import FiiDyPvpVol, FiiGeneral, FiiGeneralPrice

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
        fiis = await self.repo.get_list(
            params={"ticker_not_null": True, "ticker": ticker, "limit": 1}
        )
        fii: Fii = fiis[0]

        ticker = yf.Ticker(f"{ticker}.SA")

        return fii_in_to_out_general_price(fii, ticker.info.get("currentPrice"))
