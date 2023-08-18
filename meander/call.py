"""one-shot http client"""
import logging
import urllib.parse as urlparse

from meander.client import Client


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
    client = Client(
        host=parsed_url.host,
        port=parsed_url.port,
        is_ssl=parsed_url.is_ssl,
        verbose=verbose,
    )
    await client.open()
    client.write(
        method=method,
        path=parsed_url.path,
        query_string=parsed_url.query,
        content=content,
        headers=headers,
        content_type=content_type,
        charset=charset,
        compress=compress,
        bearer=bearer,
        close=True,
    )
    result = await client.read(timeout, active_timeout, max_read_size)
    await client.close()
    return result


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
