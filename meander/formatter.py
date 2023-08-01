"""formatters for HTTP responses"""
import gzip
import json
import time
import urllib.parse as urlparse


class HTMLFormat:  # pylint: disable=too-few-public-methods
    """form an http document"""

    def __init__(  # pylint: disable=too-many-arguments, too-few-public-methods, too-many-branches, too-many-locals, too-many-statements
        self,
        content="",
        headers=None,
        content_type=None,
        charset="utf-8",
        close=False,
        compress=False,
        is_response=True,
        # response
        code=200,
        message="",
        # request
        method="GET",
        path="/",
        query="",
        host=None,
    ):
        if is_response:
            self.code = code
            self.message = "OK" if code == 200 and message == "" else message
            self.headers = {} if not headers else headers
            self.status = f"HTTP/1.1 {self.code} {self.message}"
        else:
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
                    # pylint: disable-next=broad-exception-raised
                    raise Exception("content not allowed on GET")
                if query:
                    path += "?" + urlparse.urlencode(query)

            self.headers = headers
            self.status = f"{method} {path} HTTP/1.1"

        headers = self.headers

        header_keys = [k.lower() for k in headers.keys()]
        header_lower = {key.lower(): value for key, value in headers.items()}

        if not content_type:
            content_type = header_lower.get("content-type", None)

        if not content_type:
            if isinstance(content, int):
                content = str(content)

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
                "%a, %d %b %Y %H:%M:%S %Z", time.localtime()
            )

        if "content-length" not in header_keys:
            headers["Content-Length"] = len(content)

        if close:
            if "connection" not in header_keys:
                headers["Connection"] = "close"

        self.headers = headers
        self.content_type = content_type
        self.content = content

    def serial(self):
        """return formatted response"""
        headers = "%s\r\n%s\r\n\r\n" % (
            self.status,
            "\r\n".join([f"{k}: {v}" for k, v in self.headers.items()]),
        )
        headers = headers.encode("ascii")

        return headers + self.content if self.content else headers


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
