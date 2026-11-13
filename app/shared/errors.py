from http import HTTPStatus
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel


logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    codigo: int
    error: str
    mensaje: str


class ApiError(Exception):
    def __init__(self, status_code: int, message: str, error: str | None = None):
        self.status_code = status_code
        self.message = message
        self.error = error or HTTPStatus(status_code).phrase


def error_body(status_code: int, message: str, error: str | None = None) -> dict:
    return {"codigo": status_code, "error": error or HTTPStatus(status_code).phrase, "mensaje": message}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error_handler(_request: Request, exc: ApiError):
        return JSONResponse(status_code=exc.status_code, content=error_body(exc.status_code, exc.message, exc.error))

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_request: Request, exc: RequestValidationError):
        first = exc.errors()[0] if exc.errors() else {}
        location = ".".join(str(item) for item in first.get("loc", []) if item != "body")
        detail = first.get("msg", "Solicitud inválida")
        message = f"{location}: {detail}" if location else detail
        return JSONResponse(status_code=400, content=error_body(400, message))

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(_request: Request, exc: StarletteHTTPException):
        message = exc.detail if isinstance(exc.detail, str) else HTTPStatus(exc.status_code).phrase
        return JSONResponse(status_code=exc.status_code, content=error_body(exc.status_code, message))

    @app.exception_handler(Exception)
    async def unexpected_error_handler(_request: Request, exc: Exception):
        logger.exception("Error interno no controlado", exc_info=exc)
        return JSONResponse(status_code=500, content=error_body(500, "Ocurrió un error interno inesperado."))


async def enforce_media_types(request: Request, call_next):
    if request.method in {"POST", "PUT", "PATCH"}:
        content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        content_length = request.headers.get("content-length")
        has_body = content_length not in {None, "", "0"} or "transfer-encoding" in request.headers
        if has_body and content_type != "application/json":
            return JSONResponse(status_code=415, content=error_body(415, "Content-Type debe ser application/json."))
    accept = request.headers.get("accept", "*/*")
    accepted = {part.split(";", 1)[0].strip() for part in accept.split(",")}
    if not ({"*/*", "application/json", "application/pdf"} & accepted):
        return JSONResponse(status_code=406, content=error_body(406, "El formato solicitado no está disponible."))
    return await call_next(request)
