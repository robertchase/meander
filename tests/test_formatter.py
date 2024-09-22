"""tests for http formatter"""

import pytest

from meander.formatter import HTTPFormat


@pytest.mark.parametrize(
    "code, message, status",
    (
        (200, "", "HTTP/1.1 200 OK"),
        (200, "OK", "HTTP/1.1 200 OK"),
        (200, "HUH?", "HTTP/1.1 200 HUH?"),
        ("200", "", "HTTP/1.1 200 "),
        (400, "", "HTTP/1.1 400 "),
        (400, "Bad Request", "HTTP/1.1 400 Bad Request"),
    ),
)
def test_response_status(code, message, status):
    """test formatting of response status line"""
    fmt = HTTPFormat(code=code, message=message)
    assert fmt.status == status


@pytest.mark.parametrize(
    "method, path, query, content, status",
    (
        (None, None, None, None, "GET / HTTP/1.1"),
        ("GET", None, None, None, "GET / HTTP/1.1"),
        ("GET", "/", None, None, "GET / HTTP/1.1"),
        ("GET", "/", "", None, "GET / HTTP/1.1"),
        ("GET", "/", "", "", "GET / HTTP/1.1"),
        ("GET", "/abc", "", "", "GET /abc HTTP/1.1"),
        ("GET", "/", "a=1", "", "GET /?a=1 HTTP/1.1"),
        ("GET", "/", "", {"b": 2}, "GET /?b=2 HTTP/1.1"),
        ("GET", "/", "", {"b": [1, 2]}, "GET /?b=1&b=2 HTTP/1.1"),
    ),
)
def test_request_status(method, path, query, content, status):
    """test formatting of request status line"""
    kwargs = {
        key: val
        for key, val in (
            ("method", method),
            ("path", path),
            ("query", query),
            ("content", content),
        )
        if val is not None
    }
    fmt = HTTPFormat(is_response=False, **kwargs)
    assert fmt.status == status


def test_request_status_query_and_content():
    """verify query and content produces error for request"""
    with pytest.raises(AttributeError) as err:
        HTTPFormat(is_response=False, query="a=1", content={"b": 2})
    assert err.value.args[0] == "query string and content both specified on GET"


def test_request_status_non_dict_content():
    """verify non-dict content produces error for request"""
    with pytest.raises(AttributeError) as err:
        HTTPFormat(is_response=False, content="bad")
    assert err.value.args[0] == "expecting dict content for GET"


@pytest.mark.parametrize(
    "content, content_type, format_content",
    (
        (42, "text/plain", b"42"),
        ("42", "text/plain", b"42"),
        ([1, 2], "application/json", b"[1, 2]"),
        ({"a": 1}, "application/json", b'{"a": 1}'),
    ),
)
def test_derived_content_type(content, content_type, format_content):
    """test content-type guessing"""
    fmt = HTTPFormat(content=content)
    assert fmt.content_type == content_type + "; charset=utf-8"
    assert fmt.content == format_content


@pytest.mark.parametrize(
    "content, content_type, result",
    (
        ("", None, None),
        ("hi", None, "text/plain"),
        ([1, 2], None, "application/json"),
        ({"a": 1}, None, "application/json"),
        ({"a": 1}, "json", "application/json"),
        ({"a": 1}, "application/json", "application/json"),
        ("", "json", None),
        ("", "application/json", None),
        ({"a": 1}, "form", "application/x-www-form-urlencoded"),
        (
            {"a": 1},
            "application/x-www-form-urlencoded",
            "application/x-www-form-urlencoded",
        ),
    ),
)
def test_content_type_header(content, content_type, result):
    """test Content-Type"""
    fmt = HTTPFormat(content=content, content_type=content_type)
    if result is None:
        assert "Content-Type" not in fmt.headers
    else:
        assert fmt.headers["Content-Type"] == result + "; charset=utf-8"
