from fastapi import Query, params
from pydantic import BaseModel, ConfigDict, Field, field_serializer


class PaginatorParams(BaseModel):
    limit: int = Field(
        Query(
            50,
            title="Limit",
            description="Number of items per page",
        ),
        alias="_limit",
        ge=0,
        le=2**31 - 1,
        serialization_alias="limit",
    )
    offset: int = Field(
        Query(
            0,
            title="Offset",
            description="Offset for pagination",
        ),
        alias="_offset",
        ge=0,
        serialization_alias="offset",
        le=2**31 - 1,  # (MAXINT)
    )

    # Avoid PydanticJsonSchemaWarning: Default value is not JSON serializable
    @field_serializer("limit", "offset")
    def serialize_field(field: int | params.Query) -> int:
        """
        The parameter becomes a Query if the user omits its value, so we extract the Query default int value; if the
        user inputs the parameter, we directly return it because the value is already an integer
        To better understand this behavior, refer to L10
        """
        return field.default if isinstance(field, params.Query) else field

    model_config = ConfigDict(populate_by_name=True)


class PaginatorResponse(PaginatorParams):
    count: int = Field(description="The number of items on the current page.")
    total: int = Field(
        description="The total number of items available across all pages."
    )


class ListResponse[T](BaseModel):
    results: list[T]


class ListPaginatorResponse[T](BaseModel):
    meta: PaginatorResponse
    results: list[T]
