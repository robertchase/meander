"""one-shot http client"""
import asyncio
import logging
import urllib.parse as urlparse

from meander.parser import HTTPReader
from meander.formatter import HTMLFormat


log = logging.getLogger(__name__)


async def call(  # pylint: disable=too-many-arguments, too-many-locals
    url,
    method="GET",
    content="",
    headers=None,
    content_type=None,
    charset="utf-8",
    compress=False,
    bearer=None,
    timeout=60,
    active_timeout=5,
    max_read_size=5000,
    verbose=False,
):
    """make client call and return response"""

    parsed_url = _URL(url)

    if bearer:
        if not headers:
            headers = {}
        headers["Authorization"] = f"Bearer {bearer}"

    reader, writer = await asyncio.open_connection(
        parsed_url.host, parsed_url.port, ssl=parsed_url.is_ssl
    )
    http_reader = HTTPReader(
        reader,
        is_server=False,
        timeout=timeout,
        active_timeout=active_timeout,
        max_read_size=max_read_size,
    )

    payload = HTMLFormat(
        is_response=False,
        method=method,
        path=parsed_url.path,
        query=parsed_url.query,
        headers=headers,
        content=content,
        host=parsed_url.host,
        content_type=content_type,
        charset=charset,
        compress=compress,
    )
    writer.write(payload.serial())

    if verbose:
        log.debug(payload)

    result = await http_reader.read_document()

    if verbose:
        log.debug("%s %s", result.http_status_code, result.http_status_message)
        log.debug(result.http_headers)
        log.debug(result.http_content)

    writer.close()
    await writer.wait_closed()

    return result


def _method(name):
    """create request call bound to a method"""

    async def inner(url, *args, **kwargs):
        return await call(url, name, *args, **kwargs)

    return inner


call.get = _method("GET")
call.post = _method("POST")
call.put = _method("PUT")
call.patch = _method("PATCH")
call.delete = _method("DELETE")


class _URL:  # pylint: disable=too-few-public-methods
    """url parser"""

    def __init__(self, url):
        parsed = urlparse.urlparse(url)
        self.is_ssl = parsed.scheme == "https"
        if ":" in parsed.netloc:
            self.host, self.port = parsed.netloc.split(":", 1)
            self.port = int(self.port)
        else:
            self.host = parsed.netloc
            self.port = 443 if self.is_ssl else 80
        self.resource = parsed.path + (f"?{parsed.query if parsed.query else ''}")
        self.path = parsed.path
        self.query = parsed.query
