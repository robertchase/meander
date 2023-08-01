"""formatters for HTTP responses"""

from meander.formatter import HTMLFormat


class Response(HTMLFormat):  # pylint: disable=too-few-public-methods
    """form an http response"""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        content="",
        code=200,
        message="",
        headers=None,
        content_type=None,
        charset="utf-8",
        close=False,
        compress=False,
    ):
        super().__init__(
            code=code,
            message=message,
            headers=headers,
            content=content,
            content_type=content_type,
            charset=charset,
            close=close,
            compress=compress,
        )


class HTMLResponse(Response):  # pylint: disable=too-few-public-methods
    """form an html respose"""

    def __init__(self, content, **kwargs):
        super().__init__(
            content=content, content_type="text/html; charset=UTF-8", **kwargs
        )


class HTMLRefreshResponse(HTMLResponse):  # pylint: disable=too-few-public-methods
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
