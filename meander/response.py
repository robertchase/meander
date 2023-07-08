from meander.formatter import format_server


class Response:
    """form an html response"""
    def __init__(self, content="", code=200, message="", headers=None,
                 content_type=None, charset="utf-8", close=False,
                 compress=False):
        self.value = format_server(content, code, message, headers,
                                   content_type, charset, close, compress)


class Refresh(Response):
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
