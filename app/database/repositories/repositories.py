from app.database.models.fii import Fii
from app.database.repositories.base import BaseRepository


class FiiRepository(BaseRepository):
    model = Fii
    filtering_fields = ["ticker_not_null", "ticker"]
    ordering_fields = ["created_at"]
    default_ordering = ["created_at:desc"]
    default_limit = 50

    overwrite_where_filter = {
        "ticker_not_null": "isnot",
    }
