from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.errors import ChordAIError


def success_response(data: Any = None, message: str | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {"success": True, "data": data if data is not None else {}}
    if message:
        body["message"] = message
    return body


def error_response(code: str, message: str) -> dict[str, Any]:
    return {"success": False, "error": {"code": code, "message": message}}


async def chordai_exception_handler(_: Request, exc: ChordAIError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.code, exc.message),
    )


async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=error_response("INTERNAL_SERVER_ERROR", "Unexpected server error"),
    )
