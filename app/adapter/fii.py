from datetime import datetime

from app.database.models.fii import Fii
from app.schema.fii import FiiGeneral, FiiGeneralPrice
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
