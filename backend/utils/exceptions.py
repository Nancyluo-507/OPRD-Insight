from fastapi import Request
from fastapi.responses import JSONResponse
from utils.logger import log


class AppException(Exception):
    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code


def register_exception_handlers(app):
    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException):
        log.warning(f"{exc.status_code} {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail},
        )

    @app.exception_handler(Exception)
    async def handle_unhandled(request: Request, exc: Exception):
        log.error(f"Unhandled error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"},
        )
