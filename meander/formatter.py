"""formatter for http documents"""
import gzip
import json
import time
import urllib.parse as urlparse


def format_server(  # pylint: disable=too-many-arguments
        content="", code=200, message="", headers=None, content_type=None,
        charset="utf-8", close=False, compress=False):
    """format server http document"""

    if code == 200 and message == "":
        message = "OK"
    status = f"HTTP/1.1 {code} {message}"

    return _format(status, headers, content, content_type, charset, close,
                   compress)


def format_client(  # pylint: disable=too-many-arguments
        method="GET", path="/", query="", headers=None, content="", host=None,
        content_type=None, charset="utf-8", close=False, compress=False):
    """format client http document"""

    if host:
        if not headers:
            headers = {}
        headers["HOST"] = host

    if method == "GET":
        query = urlparse.parse_qsl(query)
        if isinstance(content, dict):
            query.extend(_normalize(content))
            content = ""
        elif content:
            raise Exception("content not allowed on GET")
        if query:
            path += "?" + urlparse.urlencode(query)

    status = f"{method} {path} HTTP/1.1"

    return _format(status, headers, content, content_type, charset, close,
                   compress)


def _format(status,  # pylint: disable=too-many-arguments,too-many-branches
            headers, content, content_type, charset, close, compress):
    """format http document"""

    if not headers:
        headers = {}

    header_keys = [k.lower() for k in headers.keys()]
    header_lower = {key.lower(): value for key, value in headers.items()}

    if not content_type:
        content_type = header_lower.get("content-type", None)

    if not content_type:
        if isinstance(content, (list, dict)):
            content_type = "application/json"
        else:
            content_type = "text/plain"

    if content:
        if "content-type" not in header_keys:
            if content_type in ("json", "application/json"):
                content = json.dumps(content)
                content_type = "application/json"
            elif content_type in ("form", "application/x-www-form-urlencoded"):
                content_type = "application/x-www-form-urlencoded"
                content = urlparse.urlencode(content)
            headers["Content-Type"] = content_type

        if charset:
            content = content.encode(charset)
            headers["Content-Type"] += f"; charset={charset}"

    if compress:
        content = gzip.compress(content)
        headers["Content-Encoding"] = "gzip"

    if "date" not in header_keys:
        headers["Date"] = time.strftime(
            "%a, %d %b %Y %H:%M:%S %Z", time.localtime())

    if "content-length" not in header_keys:
        headers["Content-Length"] = len(content)

    if close:
        if "connection" not in header_keys:
            headers["Connection"] = "close"

    headers = "%s\r\n%s\r\n\r\n" % (
        status,
        "\r\n".join(["%s: %s" % (k, v) for k, v in headers.items()]),
    )
    headers = headers.encode("ascii")

    return headers + content if content else headers


def _normalize(dct):
    """Normalize a dict into a list of tuples

       Handle the case of a dictionary value being a list or tuple by adding
       multiple tuples to the result, one for each combination of key and
       list/tuple element.
    """
    if dct == "":
        return []
    result = []
    for key, val in dct.items():
        if isinstance(val, (list, tuple)):
            for lval in val:
                result.append((key, lval))
        else:
            result.append((key, val))
    return result
