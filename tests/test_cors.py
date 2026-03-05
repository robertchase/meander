"""tests for CORS helpers"""

from meander import Request
from meander.cors import cors_after, cors_preflight
from meander.response import Response


def _request_with_origin(origin):
    """create a Request with an Origin header"""
    req = Request()
    req.http_headers = {"origin": origin}
    return req


def _request_no_origin():
    """create a Request with no Origin header"""
    req = Request()
    req.http_headers = {}
    return req


# --- cors_after tests ---


def test_cors_after_wildcard():
    """wildcard origin allows any request origin"""
    hook = cors_after(origins=["*"])
    request = _request_with_origin("https://anything.com")

    result = hook(request, "hello")
    assert isinstance(result, Response)
    assert result.headers["Access-Control-Allow-Origin"] == "*"


def test_cors_after_specific_origin():
    """matching origin is echoed back"""
    hook = cors_after(origins=["https://myapp.com"])
    request = _request_with_origin("https://myapp.com")

    result = hook(request, "hello")
    assert result.headers["Access-Control-Allow-Origin"] == "https://myapp.com"


def test_cors_after_rejects_unmatched():
    """unmatched origin gets no CORS headers"""
    hook = cors_after(origins=["https://myapp.com"])
    request = _request_with_origin("https://evil.com")

    result = hook(request, "hello")
    assert result is None


def test_cors_after_no_origin_header():
    """request without Origin header gets no CORS headers"""
    hook = cors_after()
    request = _request_no_origin()

    result = hook(request, "hello")
    assert result is None


def test_cors_after_wraps_string_result():
    """string result is wrapped in Response with CORS headers"""
    hook = cors_after()
    request = _request_with_origin("https://app.com")

    result = hook(request, "plain text")
    assert isinstance(result, Response)
    assert result.headers["Access-Control-Allow-Origin"] == "*"


def test_cors_after_preserves_response():
    """existing Response is kept, CORS headers added"""
    hook = cors_after()
    request = _request_with_origin("https://app.com")
    original = Response(content="data", headers={"X-Custom": "val"})

    result = hook(request, original)
    assert result is original
    assert result.headers["X-Custom"] == "val"
    assert result.headers["Access-Control-Allow-Origin"] == "*"


def test_cors_after_default_methods_and_headers():
    """default methods and headers are included"""
    hook = cors_after()
    request = _request_with_origin("https://app.com")

    result = hook(request, "ok")
    assert "GET" in result.headers["Access-Control-Allow-Methods"]
    assert "POST" in result.headers["Access-Control-Allow-Methods"]
    assert "Content-Type" in result.headers["Access-Control-Allow-Headers"]
    assert "Authorization" in result.headers["Access-Control-Allow-Headers"]


def test_cors_after_custom_methods():
    """custom methods override defaults"""
    hook = cors_after(methods=["GET", "HEAD"])
    request = _request_with_origin("https://app.com")

    result = hook(request, "ok")
    assert result.headers["Access-Control-Allow-Methods"] == "GET, HEAD"


def test_cors_after_custom_headers():
    """custom headers override defaults"""
    hook = cors_after(headers=["X-Api-Key"])
    request = _request_with_origin("https://app.com")

    result = hook(request, "ok")
    assert result.headers["Access-Control-Allow-Headers"] == "X-Api-Key"


def test_cors_after_multiple_origins():
    """multiple allowed origins, matching one echoes it"""
    hook = cors_after(origins=["https://a.com", "https://b.com"])

    result_a = hook(_request_with_origin("https://a.com"), "ok")
    assert result_a.headers["Access-Control-Allow-Origin"] == "https://a.com"

    result_b = hook(_request_with_origin("https://b.com"), "ok")
    assert result_b.headers["Access-Control-Allow-Origin"] == "https://b.com"

    result_c = hook(_request_with_origin("https://c.com"), "ok")
    assert result_c is None


# --- cors_preflight tests ---


def test_cors_preflight_returns_204():
    """preflight handler returns 204 with CORS headers"""
    handler = cors_preflight()
    result = handler()

    assert isinstance(result, Response)
    assert result.code == 204
    assert result.headers["Access-Control-Allow-Origin"] == "*"
    assert "GET" in result.headers["Access-Control-Allow-Methods"]


def test_cors_preflight_custom_methods():
    """preflight with custom allowed methods"""
    handler = cors_preflight(methods=["POST", "PATCH"])
    result = handler()

    assert result.headers["Access-Control-Allow-Methods"] == "POST, PATCH"


def test_cors_preflight_custom_headers():
    """preflight with custom allowed headers"""
    handler = cors_preflight(headers=["X-Token", "X-Request-Id"])
    result = handler()

    expected = "X-Token, X-Request-Id"
    assert result.headers["Access-Control-Allow-Headers"] == expected


def test_cors_preflight_max_age():
    """preflight includes max-age header"""
    handler = cors_preflight(max_age=3600)
    result = handler()

    assert result.headers["Access-Control-Max-Age"] == "3600"


def test_cors_preflight_default_max_age():
    """preflight default max-age is 86400"""
    handler = cors_preflight()
    result = handler()

    assert result.headers["Access-Control-Max-Age"] == "86400"
