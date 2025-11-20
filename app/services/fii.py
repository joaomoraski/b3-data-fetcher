from typing import Any, Coroutine

import numpy as np
import pandas as pd
import yfinance as yf
from fastapi import HTTPException
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
    FiiTccScoreResult,
    TccPreliminarResults,
    TccPreliminarSummary,
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

    async def list_fiis(self, limit: int, offset: int) -> list[FiiGeneral]:
        fiis: list[Fii] = await self.repo.get_list(
            params={"ticker_not_null": True, "limit": limit, "offset": offset}
        )

        return [fii_in_to_out_general(fii) for fii in fiis]

    async def get_one(self, ticker: str) -> FiiGeneralPrice:
        fii: Fii = await self.repo.get_by_field(f"ticker:{ticker}")
        if fii is None:
            raise HTTPException(
                status_code=404, detail=f"FII with ticker {ticker} not found"
            )

        ticker = yf.Ticker(f"{ticker}.SA")

        return fii_in_to_out_general_price(fii, ticker.info.get("currentPrice"))

    async def ticker_history(self, ticker: str) -> FiiGeneralHistory:
        fii: Fii = await self.repo.get_by_field(f"ticker:{ticker}")
        if fii is None:
            raise HTTPException(
                status_code=404, detail=f"FII with ticker {ticker} not found"
            )

        ticker = yf.Ticker(f"{ticker}.SA")

        price = ticker.info.get("currentPrice")

        fii_history = [
            fii_in_to_out_financial_history(history, price)
            for history in fii.financial_history
        ]

        return fii_in_to_out_general_history(fii, fii_history, price)

    async def ticker_history_latest(self, ticker: str) -> FiiGeneralHistory:
        fii: Fii = await self.repo.get_by_field(f"ticker:{ticker}")
        if fii is None:
            raise HTTPException(
                status_code=404, detail=f"FII with ticker {ticker} not found"
            )

        ticker = yf.Ticker(f"{ticker}.SA")

        price = ticker.info.get("currentPrice")

        fii_history = [fii_in_to_out_financial_history(fii.financial_history[0], price)]

        return fii_in_to_out_general_history(fii, fii_history, price)

    async def ticker_summary(self, ticker_name: str) -> FiiSummary:
        fii: Fii = await self.repo.get_by_field(f"ticker:{ticker_name}")
        if fii is None:
            raise HTTPException(
                status_code=404, detail=f"FII with ticker {ticker_name} not found"
            )
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

    async def _fetch_fii_data(self, tickers: list[str]) -> dict[str, dict]:
        """Fetch FII data from database and yfinance."""
        fiis: list[Fii] = [
            fii
            for ticker in tickers
            if (fii := await self.repo.get_by_field(f"ticker:{ticker}"))
        ]

        fii_data = {}
        for fii in fiis:
            if not fii.ticker or not fii.financial_history:
                continue

            fii_history = fii.financial_history[0]
            if (
                not fii_history
                or not fii_history.book_value_per_share
                or not fii_history.monthly_dividend_yield
            ):
                continue

            try:
                # Baixa 1 ano de histórico
                # investigar o que o auto_adjust faz
                df = yf.download(
                    f"{fii.ticker}.SA", period="1y", interval="1d", auto_adjust=True
                )
                if df.empty:
                    continue

                preco = float(df["Close"].iloc[-1])
                vpcota = fii_history.book_value_per_share
                pvp = preco / vpcota

                # Usa o preço de fechamento ajustado
                # Calcula retornos diários (percentuais)
                retornos = df["Close"].pct_change().dropna()
                # Calcula volatilidade anualizada
                vol_anual = float(np.std(retornos, axis=0) * np.sqrt(252))

                fii_data[fii.ticker] = {
                    "ticker": fii.ticker,
                    "dy": fii_history.monthly_dividend_yield,
                    "pvp": pvp,
                    "vol": vol_anual,
                    "preco": preco,
                }
            except Exception:
                continue

        return fii_data

    def _normalize_indicators(self, fii_data: dict[str, dict]) -> None:
        """Normalize indicators and invert P/VP (quanto menor, melhor)."""
        # separa em lista cda indicador
        dys = [fii_data[f]["dy"] for f in fii_data]
        pvps = [fii_data[f]["pvp"] for f in fii_data]
        vols = [fii_data[f]["vol"] for f in fii_data]

        # min e max
        min_dy, max_dy = min(dys), max(dys)
        min_pvp, max_pvp = min(pvps), max(pvps)
        min_vol, max_vol = min(vols), max(vols)

        # calcula normalização
        for f in fii_data:
            fii = fii_data[f]
            fii["dy_norm"] = (
                (fii["dy"] - min_dy) / (max_dy - min_dy)
                if (max_dy - min_dy) > 0
                else 0.0
            )
            fii["pvp_norm"] = (
                (fii["pvp"] - min_pvp) / (max_pvp - min_pvp)
                if (max_pvp - min_pvp) > 0
                else 0.0
            )
            fii["vol_norm"] = (
                (fii["vol"] - min_vol) / (max_vol - min_vol)
                if (max_vol - min_vol) > 0
                else 0.0
            )
            # inverter os que são "quanto menor, melhor"
            fii["pvp_norm"] = 1 - fii["pvp_norm"]

    def _calculate_scores(
        self,
        fii_data: dict[str, dict],
        alpha: float,
        beta: float,
        gamma: float,
        slot: float,
        lambda_slot: float,
    ) -> pd.DataFrame:
        """Calculate scores for all FIIs."""
        # alpha = float(input("Determine o peso de DY: "))
        # beta = float(input("Determine o peso de PVP: "))
        # gamma = float(input("Determine o peso de vol: "))
        # alpha, beta, gamma = 0.5, 0.3, 0.2
        # B = 400
        # K = 2
        # lambda_slot = 0.1

        data = []
        for f in fii_data:
            fii = fii_data[f]
            penalidade_slot = max(0, fii["preco"] - slot)
            score = (
                alpha * fii["dy_norm"]
                + beta * fii["pvp_norm"]
                - gamma * fii["vol_norm"]
                - lambda_slot * penalidade_slot
            )
            data.append(
                {
                    "Ticker": fii["ticker"],
                    "DY (normalizado)": round(fii["dy_norm"], 3),
                    "P/VP (normalizado)": round(fii["pvp_norm"], 3),
                    "Volatilidade (normalizado)": round(fii["vol_norm"], 3),
                    "Preço (R$)": round(fii["preco"], 3),
                    "Penalidade Slot": round(penalidade_slot, 2),
                    "Score": round(score, 3),
                }
            )

        df = pd.DataFrame(data)
        return df.sort_values("Score", ascending=False).reset_index(drop=True)

    def _build_response(
        self, df: pd.DataFrame, topK: pd.DataFrame, B: float, slot: float
    ) -> TccPreliminarResults:
        """Build the response object from calculated data."""
        total_preco = topK["Preço (R$)"].sum()
        status = "Dentro do orçamento" if total_preco <= B else "Violou orçamento"

        def _row_to_result(row: pd.Series) -> FiiTccScoreResult:
            return FiiTccScoreResult(
                ticker=row["Ticker"],
                dy_normalizado=row["DY (normalizado)"],
                pvp_normalizado=row["P/VP (normalizado)"],
                volatilidade_normalizado=row["Volatilidade (normalizado)"],
                preco=row["Preço (R$)"],
                penalidade_slot=row["Penalidade Slot"],
                score=row["Score"],
            )

        return TccPreliminarResults(
            all_results=[_row_to_result(row) for _, row in df.iterrows()],
            top_k_results=[_row_to_result(row) for _, row in topK.iterrows()],
            summary=TccPreliminarSummary(
                total_preco=round(float(total_preco), 2),
                orcamento=B,
                limite_por_ativo=slot,
                status=status,
                top_k_tickers=list(topK["Ticker"]),
            ),
        )

    async def tcc_preliminar_results(
        self,
        alpha: float = 0.5,
        beta: float = 0.3,
        gamma: float = 0.2,
        B: float = 400.0,
        K: int = 2,
        lambda_slot: float = 0.1,
        tickers: list[str] | None = None,
    ) -> TccPreliminarResults:
        # Use default tickers if none provided
        tickers = tickers or ["MXRF11", "XPML11", "HGLG11", "BTHF11"]

        fii_data = await self._fetch_fii_data(tickers)
        if not fii_data:
            return TccPreliminarResults(
                all_results=[],
                top_k_results=[],
                summary=TccPreliminarSummary(
                    total_preco=0.0,
                    orcamento=B,
                    limite_por_ativo=B / K if K > 0 else 0.0,
                    status="Nenhum FII disponível",
                    top_k_tickers=[],
                ),
            )

        self._normalize_indicators(fii_data)
        slot = B / K
        df = self._calculate_scores(fii_data, alpha, beta, gamma, slot, lambda_slot)
        topK = df.head(K)

        return self._build_response(df, topK, B, slot)
