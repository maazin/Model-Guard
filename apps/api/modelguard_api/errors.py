"""RFC 7807 problem-details errors."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from modelguard_governance.lifecycle import TransitionError


class Problem(Exception):
    def __init__(
        self,
        status: int,
        title: str,
        detail: str,
        *,
        type_: str = "about:blank",
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(detail)
        self.status = status
        self.title = title
        self.detail = detail
        self.type = type_
        self.extra = extra or {}


def not_found(entity: str, ident: str) -> Problem:
    return Problem(404, "Not found", f"{entity} '{ident}' does not exist", type_="urn:modelguard:not-found")


def forbidden(detail: str) -> Problem:
    return Problem(403, "Forbidden", detail, type_="urn:modelguard:forbidden")


def conflict(detail: str, extra: dict[str, Any] | None = None) -> Problem:
    return Problem(409, "Conflict", detail, type_="urn:modelguard:conflict", extra=extra)


def bad_request(detail: str, extra: dict[str, Any] | None = None) -> Problem:
    return Problem(400, "Bad request", detail, type_="urn:modelguard:bad-request", extra=extra)


def _problem_response(
    request: Request, status: int, title: str, detail: str, type_: str, extra: dict[str, Any]
) -> JSONResponse:
    body = {
        "type": type_,
        "title": title,
        "status": status,
        "detail": detail,
        "instance": str(request.url.path),
        **extra,
    }
    return JSONResponse(status_code=status, content=body, media_type="application/problem+json")


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(Problem)
    async def _problem(request: Request, exc: Problem) -> JSONResponse:
        return _problem_response(request, exc.status, exc.title, exc.detail, exc.type, exc.extra)

    @app.exception_handler(TransitionError)
    async def _transition(request: Request, exc: TransitionError) -> JSONResponse:
        status = 403 if exc.code == "forbidden" else 409
        return _problem_response(request, status, "Lifecycle rule violated", str(exc), f"urn:modelguard:{exc.code}", {})

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        return _problem_response(
            request,
            422,
            "Validation error",
            "Request body or parameters are invalid",
            "urn:modelguard:validation",
            {"errors": exc.errors()},
        )
