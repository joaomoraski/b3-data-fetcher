from functools import wraps
from typing import Any, Type
from uuid import UUID

from sqlalchemy import and_, asc, desc, func, select
from sqlalchemy import column as sa_column
from sqlalchemy import distinct as sa_distinct
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.exceptions.ExceptionBase import ConflictException


class BaseModel(DeclarativeBase):
    pass


def conflict_if_exists(f):
    @wraps(f)
    async def inner(*args, **kwargs):
        try:
            return await f(*args, **kwargs)
        except IntegrityError as err:
            if "already exists" in str(err):
                raise ConflictException("already exists")
            raise

    return inner


class BaseRepository:
    model: Type[DeclarativeBase]
    filtering_fields: list[str]
    ordering_fields: list[str]
    default_ordering: list[str]
    default_limit: int

    overwrite_where_filter: dict[str, str]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        mandatory_attrs_check = [
            "model",
            "filtering_fields",
            "ordering_fields",
            "default_ordering",
            "default_limit",
            "overwrite_where_filter",
        ]
        for attr in mandatory_attrs_check:
            assert hasattr(
                self, attr
            ), f'The "{attr}" should be defined in "{self.__class__.__name__}"'

    def _filter_where_fields(self, fields: dict[str, str]) -> dict:
        result = {}
        for name, value in fields.items():
            # suporte a campos virtuais
            if name.endswith("_not_null"):
                base_name = name.removesuffix("_not_null")
                if hasattr(self.model, base_name) and name in self.filtering_fields:
                    result[name] = value
                continue

            if not hasattr(self.model, name) or name not in self.filtering_fields:
                continue

            result[name] = value

        return result

    def _filter_sort_fields(self, fields: list[str]) -> list[Any]:
        result = []
        for item in fields:
            name, _ = item.split(":", 1)
            if not hasattr(self.model, name) or name not in self.ordering_fields:
                continue

            result.append(item)

        return result or self.default_ordering

    def _get_where_filters(self, fields: dict[str, str]) -> list[Any]:
        filters = []
        for key, value in fields.items():
            if key.endswith("_not_null"):
                real_column = key.replace("_not_null", "")
                column = getattr(self.model, real_column)
                filters.append(column.isnot(None))
                continue

            column = getattr(self.model, key)
            where_operator = getattr(
                column, self.overwrite_where_filter.get(key, "__eq__")
            )
            filters.append(where_operator(value))
        return filters

    def _get_order_by_filters(self, fields: list[str]) -> list[Any]:
        result = []
        for item in fields:
            name, order = item.split(":", 1)
            column = sa_column(name)
            ordering = asc(column) if order == "asc" else desc(column)
            result.append(ordering)

        return result

    def _get_only_filters(self, fields: list[str]) -> list[Any]:
        if not fields:
            return [self.model]

        return [
            getattr(self.model, field) for field in fields if hasattr(self.model, field)
        ]

    async def get_list(self, params: dict | None = None) -> list[DeclarativeBase]:
        if not params:
            params = {}

        distinct = params.pop("distinct", False)
        limit = params.pop("limit", self.default_limit)
        offset = params.pop("offset", None)
        sort = params.pop("sort", [])
        sort = self._filter_sort_fields(sort)

        only_fields = params.pop("only", [])
        only_filters = self._get_only_filters(only_fields)

        where_fields = self._filter_where_fields(params)
        where_filters = self._get_where_filters(where_fields)

        statement = select(*only_filters)
        if distinct:
            statement = statement.distinct()
        if where_fields:
            statement = statement.where(and_(*where_filters))

        order_filters = self._get_order_by_filters(sort)
        statement = statement.order_by(*order_filters)

        statement = statement.limit(limit)
        if offset:
            statement = statement.offset(offset)

        return (await self._session.scalars(statement)).all()

    async def get(self, id: UUID | str) -> DeclarativeBase:
        return await self._session.get(self.model, id)

    async def get_by_field(self, filter: str) -> DeclarativeBase:
        column_name, value = filter.split(":", 1)
        column = getattr(self.model, column_name)
        statement = select(self.model).where(column == value)
        return await self._session.scalar(statement)

    async def create(self, entity: DeclarativeBase) -> DeclarativeBase:
        self._session.add(entity)
        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def update(self, entity: DeclarativeBase) -> DeclarativeBase:
        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def delete(self, entity: DeclarativeBase) -> DeclarativeBase:
        await self._session.delete(entity)
        await self._session.commit()
        return entity

    async def count(self, params: dict | None = None) -> int:
        if not params:
            params = {}

        distinct = params.pop("distinct", False)
        only_fields = params.pop("only", [])

        where_fields = self._filter_where_fields(params)
        where_filters = self._get_where_filters(where_fields)

        count_statement = func.count()
        if distinct:
            only_filters = self._get_only_filters(only_fields)
            count_statement = func.count(sa_distinct(*only_filters))

        statement = select(count_statement).select_from(self.model)

        if where_fields:
            statement = statement.where(and_(*where_filters))

        return await self._session.scalar(statement)
