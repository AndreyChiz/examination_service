import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.openapi.utils import get_openapi
from fastapi.responses import ORJSONResponse

from api import root_api_router
from api.middlewares import LogRequestsMiddleware
from config import settings
from core.database import db_master
from logger import CustomLogger


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await db_master.dispose()


main_app = FastAPI(
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

logger = CustomLogger.make_logger(**settings.logger.model_dump())
main_app.logger = logger

main_app.include_router(
    root_api_router,
    prefix=settings.api.prefix,
)


main_app.add_middleware(
    LogRequestsMiddleware,
)


def custom_openapi():
    """The bug with default server path overriding in openapi v3.2.0
    needs to set to v3.0.0 by this function"""
    if main_app.openapi_schema:
        return main_app.openapi_schema
    openapi_schema = get_openapi(
        title=settings.api.v1.openapi.title,
        version=settings.api.v1.openapi.doc_version,
        description=settings.api.v1.openapi.description,
        routes=main_app.routes,
    )
    openapi_schema["openapi"] = settings.api.v1.openapi.version
    main_app.openapi_schema = openapi_schema
    return main_app.openapi_schema


main_app.openapi = custom_openapi


if __name__ == "__main__":

    uvicorn.run(
        "main:main_app",
        host=settings.run.host,
        port=settings.run.port,
        reload=True,
        # log_config=None,  # Отключить конфигурацию логов Uvicorn
        # access_log=False,  # Отключить access log
        # use_colors=False,
    )
