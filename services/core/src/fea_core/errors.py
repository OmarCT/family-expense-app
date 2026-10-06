from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from fea_core.i18n import translate

HTTP_CODES = {401: "unauthorized", 404: "not_found", 409: "stale_revision", 503: "auth_unavailable"}


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, current_revision: int | None = None) -> None:
        super().__init__(code)
        self.status_code = status_code
        self.code = code
        self.current_revision = current_revision


def _response(
    request: Request,
    status_code: int,
    code: str,
    current_revision: int | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body: dict[str, object] = {
        "code": code,
        "message": translate(f"error.{code}", request.headers.get("accept-language", "es-MX")[:5]),
        "correlation_id": getattr(request.state, "correlation_id", ""),
    }
    if current_revision is not None:
        body["current_revision"] = current_revision
    return JSONResponse(body, status_code=status_code, headers=headers)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error(request: Request, exc: ApiError) -> JSONResponse:
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
        return _response(request, exc.status_code, exc.code, exc.current_revision, headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, _exc: RequestValidationError) -> JSONResponse:
        return _response(request, 422, "validation_error")

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _response(request, exc.status_code, HTTP_CODES.get(exc.status_code, "http_error"))
