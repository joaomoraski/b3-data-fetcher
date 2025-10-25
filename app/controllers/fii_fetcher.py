from fastapi import APIRouter

from app.schema.fii import AtivoSchema
from app.services.fii import FiiFetcherService

router = APIRouter(prefix="/fii", tags=["fii"])


@router.get("/get-one-ticker/")
async def get_one_ticker(ticker: str, cnpj: str) -> AtivoSchema:
    fii_service = FiiFetcherService()
    return await fii_service.fetch(ticker, cnpj)
