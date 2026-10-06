import time
from typing import Annotated
from uuid import UUID, uuid4

import structlog
from fastapi import APIRouter, Depends, FastAPI, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from fea_core.auth import (
    Auth0TokenVerifier,
    AuthUnavailableError,
    InvalidTokenError,
    Principal,
    TokenVerifier,
)
from fea_core.config import Settings
from fea_core.errors import ApiError, register_error_handlers
from fea_core.logging_setup import configure_logging
from fea_core.telemetry import configure_tracing

DEFAULT_LOCALE = "es-MX"
CORRELATION_HEADER = "X-Correlation-Id"

logger = structlog.get_logger()
bearer = HTTPBearer(auto_error=False)


def get_principal(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> Principal:
    if credentials is None:
        raise ApiError(401, "unauthorized")
    verifier: TokenVerifier = request.app.state.verifier
    try:
        return verifier.verify(credentials.credentials)
    except InvalidTokenError as exc:
        raise ApiError(401, "unauthorized") from exc
    except AuthUnavailableError as exc:
        raise ApiError(503, "auth_unavailable") from exc


router = APIRouter()


@router.get("/health", operation_id="getHealth", summary="Estado del servicio")
def get_health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/me", operation_id="getMe", summary="Usuario autenticado")
def get_me(principal: Annotated[Principal, Depends(get_principal)]) -> dict[str, str]:
    return {"id": str(principal.user_id), "locale": DEFAULT_LOCALE}


def _correlation_id(request: Request) -> str:
    candidate = request.headers.get(CORRELATION_HEADER, "")
    try:
        return str(UUID(candidate))
    except ValueError:
        return str(uuid4())


def create_app(
    settings: Settings | None = None,
    verifier: TokenVerifier | None = None,
    configure_observability: bool = True,
) -> FastAPI:
    settings = settings or Settings()
    if configure_observability:
        configure_logging(settings.log_level)
        configure_tracing("fea-core", settings.environment)

    app = FastAPI(title="Family Expense API", version="1.0.0")
    app.state.verifier = verifier or Auth0TokenVerifier(
        settings.issuer, settings.auth0_audience, settings.jwks_url
    )
    register_error_handlers(app)

    @app.middleware("http")
    async def correlation_and_access_log(request: Request, call_next):  # type: ignore[no-untyped-def]
        correlation_id = _correlation_id(request)
        request.state.correlation_id = correlation_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
        started = time.perf_counter()
        response: Response = await call_next(request)
        response.headers[CORRELATION_HEADER] = correlation_id
        route = request.scope.get("route")
        logger.info(
            "request",
            method=request.method,
            route=getattr(route, "path", "unmatched"),
            status=response.status_code,
            duration_ms=round((time.perf_counter() - started) * 1000, 1),
        )
        return response

    app.include_router(router, prefix="/v1")
    return app
