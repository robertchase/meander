"""demonstrate before processing"""
import logging

import meander as web


logging.basicConfig(level=logging.INFO)


def value(value: str):
    return value


def header(header_name, content_name, default=None):
    """add the value of header_name to request.content

    if header_name is not present use default
    if header_name is not present and default is None, 400 Bad Request
    """
    def _header(request):
        if not (value := request.http_headers.get(header_name, default)):
            raise web.HTTPException(400, "Bad Request", f"missing header {header_name}")
        if not (content := request.content):
            content = {}
        content[content_name] = value
        request.content = content
    return _header


(web.add_server()
    .add_route("/value", value, before=header("x-value", "value", "default-value"))
    .add_route("/value/required", value, before=header("x-value", "value"))
)
web.run()
