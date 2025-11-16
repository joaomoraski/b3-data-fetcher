from sqlalchemy import desc, func, select
from sqlalchemy.orm import aliased

from app.database.models.fii import Fii, FiiFinancialHistory
from app.database.repositories.base import BaseRepository


class FiiRepository(BaseRepository):
    model = Fii
    filtering_fields = ["ticker_not_null", "ticker", "dy_not_null"]
    ordering_fields = ["created_at", "financial_history.monthly_dividend_yield"]
    default_ordering = ["created_at:desc"]
    default_limit = 50

    overwrite_where_filter = {
        "ticker_not_null": "isnot",
        "dy_not_null": "isnot",
    }

    async def get_list(self, params: dict | None = None) -> list[Fii]:
        return await BaseRepository.get_list(self, params)

    async def ranking_dy(self, limit: int, offset: int):
        h = aliased(FiiFinancialHistory)

        # DISTINCT ON – pegar a linha mais recente por FII
        sub = (
            select(
                h.fii_id,
                Fii.name,
                Fii.ticker,
                h.reference_date,
                h.monthly_dividend_yield,
                h.book_value_per_share,
            )
            .join(Fii, Fii.id == h.fii_id)
            .where(Fii.ticker.is_not(None))
            .where(h.monthly_dividend_yield.is_not(None))
            .order_by(
                h.fii_id,
                h.reference_date.desc(),
            )
            .distinct(h.fii_id)
            .subquery()
        )

        stmt = (
            select(Fii, sub)
            .join(sub, sub.c.fii_id == Fii.id)
            .order_by(sub.c.monthly_dividend_yield.desc())
            .limit(limit)
            .offset(offset)
        )

        rows = (await self._session.execute(stmt)).all()

        return rows
