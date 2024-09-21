"""formatters for HTTP documents"""

from dataclasses import dataclass
import gzip
import json
import time
from typing import Any
import urllib.parse as urlparse


@dataclass
class HTTPFormat:  # pylint: disable=too-many-instance-attributes
    """format an http document"""

    content: Any = ""

    code: int = 200  # response
    message: str = ""  # response

    headers: dict = None
    content_type: str = None
    charset: str = "utf-8"
    close: bool = False
    compress: bool = False
    is_response: bool = True

    # request
    method: str = "GET"
    path: str = "/"
    query: dict | str = ""
    host: str = None

    def __post_init__(self):
        self.headers = {} if not self.headers else self.headers
        if self.is_response:
            self.fmt_response()
        else:
            self.fmt_request()
        self.fmt_common()

    def fmt_response(self):
        """response specific formatting"""

        self.message = "OK" if self.code == 200 and self.message == "" else self.message
        self.status = f"HTTP/1.1 {self.code} {self.message}"

    def fmt_request(self):
        """request specific formatting"""
        if self.host:
            self.headers["HOST"] = self.host

        if self.method == "GET":
            if self.content:
                if self.query:
                    raise AttributeError(
                        "query string and content both specified on GET"
                    )
                if not isinstance(self.content, dict):
                    raise AttributeError("expecting dict content for GET")
                self.query = _normalize(self.content)
                self.content = ""
            else:
                self.query = urlparse.parse_qsl(self.query)
            if self.query:
                self.path += "?" + urlparse.urlencode(self.query)

        self.status = f"{self.method} {self.path} HTTP/1.1"

    def fmt_common(self):
        """format items common to both response and request documents"""

        header_lower = {key.lower(): value for key, value in self.headers.items()}
        if self.content:
            self.fmt_content(header_lower)
        else:
            self.content_type = None
        self.fmt_headers(header_lower)

    def fmt_content(self, header_lower):
        """normalize content and content_type

        focus primarily on form and json content in order to help with
        json/http exchanges. other content types will pass through unscathed.
        """

        if not self.content_type:
            self.content_type = header_lower.get("content-type", None)

        if not self.content_type:
            if isinstance(self.content, int):
                self.content = str(self.content)

            if isinstance(self.content, (list, dict)):
                self.content_type = "application/json"
            else:
                self.content_type = "text/plain"

        if self.content_type in ("json", "application/json"):
            self.content = json.dumps(self.content)
            self.content_type = "application/json"
        elif self.content_type in ("form", "application/x-www-form-urlencoded"):
            self.content_type = "application/x-www-form-urlencoded"
            self.content = urlparse.urlencode(self.content)

        if self.charset:
            self.content = self.content.encode(self.charset)
            self.content_type += f"; charset={self.charset}"

        if self.compress:
            self.content = gzip.compress(self.content)

    def fmt_headers(self, header_lower):
        """add some standard headers"""

        if self.content_type:
            self.headers["Content-Type"] = self.content_type

        if self.compress:
            self.headers["Content-Encoding"] = "gzip"

        if "date" not in header_lower:
            self.headers["Date"] = time.strftime(
                "%a, %d %b %Y %H:%M:%S %Z", time.localtime()
            )

        if "content-length" not in header_lower:
            self.headers["Content-Length"] = len(self.content)

        if self.close:
            if "connection" not in header_lower:
                self.headers["Connection"] = "close"

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
