import gzip
import json
import time
import urllib.parse as urlparse


class Response:
    """form an http response"""
    def __init__(self, content="", code=200, message="", headers=None,
                 content_type=None, charset="utf-8", close=False,
                 compress=False):
        self.code = code
        self.message = "OK" if code == 200 and message == "" else message
        self.headers = {} if not headers else headers
        self.status = f"HTTP/1.1 {self.code} {self.message}"
        self.normalize(content, content_type, charset, close, compress)

    def normalize(self, content, content_type, charset, close, compress):

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
                elif content_type in (
                        "form", "application/x-www-form-urlencoded"):
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

        self.headers = headers
        self.content_type = content_type
        self.content = content

    def serial(self):
        headers = "%s\r\n%s\r\n\r\n" % (
            self.status,
            "\r\n".join(["%s: %s" % (k, v) for k, v in self.headers.items()]),
        )
        headers = headers.encode("ascii")

        return headers + self.content if self.content else headers


class ClientResponse(Response):

    def __init__(self, method="GET", path="/", query="", headers=None,
                 content="", host=None, content_type=None, charset="utf-8",
                 close=False, compress=False):

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

        self.headers = headers
        self.status = f"{method} {path} HTTP/1.1"
        self.normalize(content, content_type, charset, close, compress)


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


class HTMLResponse(Response):
    """form and html respose"""
    def __init__(self, content, **kwargs):
        super().__init__(
            content=content,
            content_type="text/html; charset=UTF-8",
            **kwargs)


class HTMLRefreshResponse(HTMLResponse):
    """form an html refresh response"""
    def __init__(self, url):
        super().__init__(
            "<html>"
            "<head>"
            f'<meta http-equiv="Refresh" content="0; url=\'{url}\'" />'
            "</head>"
            "<body></body>"
            "</html>"
        )
