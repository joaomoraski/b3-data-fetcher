from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db_session
from app.schema.fii import FiiSchema
from app.services.fii import FiiFetcherService

router = APIRouter(prefix="/fii", tags=["fii"])


@router.get("/get-one-ticker/")
async def get_one_ticker(
    ticker: str, session: AsyncSession = Depends(get_db_session)
) -> FiiSchema:
    fii_service = FiiFetcherService(session)
    return await fii_service.fetch(ticker.upper())
