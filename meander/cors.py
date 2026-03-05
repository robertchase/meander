"""CORS (Cross-Origin Resource Sharing) helpers.

Provides factory functions that produce after hooks and handlers
for adding CORS headers to HTTP responses.
"""

from collections.abc import Callable
from typing import Any

from meander.response import Response

DEFAULT_METHODS = ["GET", "POST", "PUT", "DELETE"]
DEFAULT_HEADERS = ["Content-Type", "Authorization"]


def cors_after(
    origins: list[str] | None = None,
    methods: list[str] | None = None,
    headers: list[str] | None = None,
) -> Callable:
    """Return an after hook that adds CORS headers to responses.

    origins - list of allowed origins, or ["*"] to allow any (default)
    methods - list of allowed HTTP methods
    headers - list of allowed request headers
    """
    allowed_origins = origins or ["*"]
    allowed_methods = ", ".join(methods or DEFAULT_METHODS)
    allowed_headers = ", ".join(headers or DEFAULT_HEADERS)

    def after(request: Any, result: Any) -> Response:
        """add CORS headers if the request origin is allowed"""
        origin = request.http_headers.get("origin")
        if not origin:
            return None

        if "*" in allowed_origins:
            allow_origin = "*"
        elif origin in allowed_origins:
            allow_origin = origin
        else:
            return None

        if not isinstance(result, Response):
            result = Response(result)
        result.headers["Access-Control-Allow-Origin"] = allow_origin
        result.headers["Access-Control-Allow-Methods"] = allowed_methods
        result.headers["Access-Control-Allow-Headers"] = allowed_headers
        return result

    return after


def cors_preflight(
    origins: list[str] | None = None,
    methods: list[str] | None = None,
    headers: list[str] | None = None,
    max_age: int = 86400,
) -> Callable:
    """Return a handler for OPTIONS preflight requests.

    origins - list of allowed origins, or ["*"] to allow any (default)
    methods - list of allowed HTTP methods
    headers - list of allowed request headers
    max_age - seconds the browser can cache the preflight result
    """
    allowed_origins = origins or ["*"]
    allowed_methods = ", ".join(methods or DEFAULT_METHODS)
    allowed_headers = ", ".join(headers or DEFAULT_HEADERS)

    def handler(request: Any = None) -> Response:
        """respond to OPTIONS preflight with CORS headers"""
        origin = "*"
        if request and hasattr(request, "http_headers"):
            req_origin = request.http_headers.get("origin", "")
            if "*" not in allowed_origins:
                if req_origin in allowed_origins:
                    origin = req_origin
                else:
                    return Response(code=204, message="No Content")
            else:
                origin = "*"

        return Response(
            code=204,
            message="No Content",
            headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": allowed_methods,
                "Access-Control-Allow-Headers": allowed_headers,
                "Access-Control-Max-Age": str(max_age),
            },
        )

    return handler
