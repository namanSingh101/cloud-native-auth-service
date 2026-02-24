from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# from slowapi import _rate_limit_exceeded_handler
from app.core import get_settings, limiter, AppException
from app.exception_handler import app_exception_handler, http_exception_handler, validation_exception_handler, rate_limit_exceeded_handler, unhandled_exception_handler
from app.api import v1_router


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        AppException, app_exception_handler)  # type: ignore
    app.add_exception_handler(StarletteHTTPException,
                              http_exception_handler)  # type: ignore
    app.add_exception_handler(RequestValidationError,
                              validation_exception_handler)  # type: ignore
    app.add_exception_handler(
        RateLimitExceeded, rate_limit_exceeded_handler)  # type: ignore
    # removed because it is giving issue of duplicate logs
    app.add_exception_handler(Exception, unhandled_exception_handler)


def create_app() -> FastAPI:
    # geting configuration
    settings = get_settings()

    # app creation
    app = FastAPI(
        title="Backend Api",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json"
    )

    # setting limiter
    app.state.limiter = limiter

    # routers
    app.include_router(v1_router, prefix=settings.API_PREFIX)

    # exception handler
    register_exception_handlers(app=app)

    # middleware
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
        max_age=3600
    )  # register last but will run first when request comes in

    return app


app = create_app()
