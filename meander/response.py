"""formatters for HTTP responses"""

from dataclasses import dataclass

from meander.formatter import HTTPFormat as Response


@dataclass
class HTMLResponse(Response):
    """form an html response (handy shortcut)"""

    content_type: str = "text/html"


class HTMLRefreshResponse(HTMLResponse):
    """form an html refresh response given a refresh url"""

    def __init__(self, url):
        super().__init__(
            "<html>"
            "<head>"
            f'<meta http-equiv="Refresh" content="0; url=\'{url}\'" />'
            "</head>"
            "<body></body>"
            "</html>"
        )
