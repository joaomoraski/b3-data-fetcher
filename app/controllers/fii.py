from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db_session
from app.schema.fii import (
    FiiDyPvpVol,
    FiiGeneral,
    FiiGeneralHistory,
    FiiGeneralPrice,
    FiiSummary,
    RankingDy,
)
from app.schema.Paginator import (
    ListPaginatorResponse,
    PaginatorParams,
    PaginatorResponse,
)
from app.services.fii import FiiService

router = APIRouter(prefix="/fii", tags=["fii"])


# http://127.0.0.1:8080/api/v1/fii/tcc?ticker=mxrf11
@router.get("/tcc", include_in_schema=False)
async def tcc(
    ticker: str, session: AsyncSession = Depends(get_db_session)
) -> FiiDyPvpVol:
    fii_service = FiiService(session)
    return await fii_service.tcc(ticker.upper())


@router.get("/")
async def get_fiis(
    paginator_qs: PaginatorParams = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> ListPaginatorResponse[FiiGeneral]:
    fii_service = FiiService(session)
    fii_list = await fii_service.list(
        limit=paginator_qs.limit, offset=paginator_qs.offset
    )
    count = await fii_service.count()

    paginator = PaginatorResponse(
        offset=paginator_qs.offset,
        limit=paginator_qs.limit,
        count=count,
        total=len(fii_list),
    )
    return ListPaginatorResponse(results=fii_list, meta=paginator)


@router.get("/{ticker}")
async def get_ticker(
    ticker: str, session: AsyncSession = Depends(get_db_session)
) -> FiiGeneralPrice:
    fii_service = FiiService(session)
    fii = await fii_service.get_one(ticker.upper())

    return fii


@router.get("/{ticker}/history")
async def get_ticker_history(
    ticker: str, session: AsyncSession = Depends(get_db_session)
) -> FiiGeneralHistory:
    fii_service = FiiService(session)
    fii = await fii_service.ticker_history(ticker.upper())

    return fii


@router.get("/{ticker}/history/latest")
async def get_ticker_history_latest(
    ticker: str, session: AsyncSession = Depends(get_db_session)
) -> FiiGeneralHistory:
    fii_service = FiiService(session)
    fii = await fii_service.ticker_history_latest(ticker.upper())

    return fii


@router.get("/{ticker}/summary")
async def get_ticker_summary(
    ticker: str, session: AsyncSession = Depends(get_db_session)
) -> FiiSummary:
    fii_service = FiiService(session)
    fii = await fii_service.ticker_summary(ticker.upper())

    return fii


#### Ranking ####


@router.get("/ranking/dy")
async def get_ranking_dy(
    paginator_qs: PaginatorParams = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> ListPaginatorResponse[RankingDy]:
    fii_service = FiiService(session)
    ranking_dy = await fii_service.ranking_dy(
        paginator_qs.limit, offset=paginator_qs.offset
    )
    count = await fii_service.count()

    paginator = PaginatorResponse(
        offset=paginator_qs.offset,
        limit=paginator_qs.limit,
        count=count,
        total=len(ranking_dy),
    )
    return ListPaginatorResponse(results=ranking_dy, meta=paginator)
