"""http client"""
import asyncio
from functools import partial
import logging
import urllib.parse as urllib

from meander.parser import HTTPReader
from meander.response import ClientResponse


log = logging.getLogger(__name__)


class Client:  # pylint: disable=too-many-instance-attributes
    """http client"""

    def __init__(self, url):
        self.url = _URL(url)
        self.reader = None
        self.writer = None
        self.read = None
        self.payload = None

        self.get = partial(self.execute, "GET")
        self.post = partial(self.execute, "POST")
        self.put = partial(self.execute, "PUT")
        self.patch = partial(self.execute, "PATCH")
        self.delete = partial(self.execute, "DELETE")

    async def open(self, timeout=60, active_timeout=5, max_read_size=5000):
        """open the connection"""
        reader, writer = await asyncio.open_connection(
            self.url.host, self.url.port, ssl=self.url.is_ssl
        )
        self.writer = writer
        http_reader = HTTPReader(
            reader,
            is_server=False,
            timeout=timeout,
            active_timeout=active_timeout,
            max_read_size=max_read_size,
        )
        self.read = http_reader.read_document

    async def close(self):
        """close the connection"""
        self.writer.close()
        await self.writer.wait_closed()

    def write(  # pylint: disable=too-many-arguments
        self,
        method="GET",
        path="/",
        query="",
        headers=None,
        content="",
        host=None,
        content_type=None,
        charset="utf-8",
        close=False,
        compress=False,
    ):
        """send an HTTP document on the connection"""
        self.payload = ClientResponse(
            method=method,
            path=path,
            query=query,
            headers=headers,
            content=content,
            host=host,
            content_type=content_type,
            charset=charset,
            close=close,
            compress=compress,
        )
        self.writer.write(self.payload.serial())

    async def execute(  # pylint: disable=too-many-arguments
        self,
        method,
        path="/",
        query="",
        content="",
        host=None,
        headers=None,
        close=False,
    ):
        """make an HTTP call and return the response"""
        self.write(method, path, query, content, host, headers, close)
        return await self.read()


async def call(  # pylint: disable=too-many-arguments
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

    if bearer:
        if not headers:
            headers = {}
        headers["Authorization"] = f"Bearer {bearer}"

    client = Client(url)
    await client.open(
        timeout=timeout, active_timeout=active_timeout, max_read_size=max_read_size
    )
    client.write(
        method=method,
        path=client.url.path,
        query=client.url.query,
        headers=headers,
        content=content,
        host=client.url.host,
        content_type=content_type,
        charset=charset,
        close=True,
        compress=compress,
    )
    if verbose:
        log.debug(client.payload)

    result = await client.read()
    if verbose:
        log.debug("%s %s", result.http_status_code, result.http_status_message)
        log.debug(result.http_headers)
        log.debug(result.http_content)

    await client.close()
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
        parsed = urllib.urlparse(url)
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
