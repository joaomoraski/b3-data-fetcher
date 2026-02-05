from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.routers import routers


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    docs_url="/docs",
    swagger_ui_parameters={
        "displayRequestDuration": True,
        "persistAuthorization": True,
    },
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in routers:
    app.include_router(router=router, prefix=settings.API_V1_STR)
