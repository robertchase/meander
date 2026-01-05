"""one-shot http client"""

import asyncio
import logging
from urllib.parse import urlparse

from meander.client import Client
from meander import document
from meander import retry_policy


log = logging.getLogger(__name__)


async def call(  # pylint: disable=too-many-arguments, too-many-locals
    url,
    content="",
    headers: dict | None=None,
    content_type: str | None=None,
    charset: str="utf-8",
    compress: bool=False,
    bearer: str | None=None,
    timeout: int=60,
    active_timeout: int=5,
    max_read_size: int=5000,
    method: str="GET",
    verbose: bool=False,
    retry: bool | retry_policy.RetryPolicy | None=None,
) -> document.ClientDocument:
    """Make an HTTP call and return the response in a ClientDocument.

    The payload sent to the server is saved in the returned ClientDocument as the
    'request' attribute.
    """

    parsed_url = _URL(url)
    if retry is True:
        retry = retry_policy.RetryPolicy()

    async def _call():
        client = Client(verbose=verbose)
        await client.open(parsed_url.host, parsed_url.port, is_ssl=parsed_url.is_ssl)
        payload = client.write(
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
        result.request = payload
        await client.close()
        return result

    while True:
        response = await _call()
        status_code = response.http_status_code
        headers = response.http_headers

        if status_code in (301, 302) and "location" in headers:
            new_url = _URL(headers["location"])
            parsed_url.host = new_url.host
            parsed_url.is_ssl = new_url.is_ssl

        elif retry and (delay := retry(status_code)):
            await asyncio.sleep(delay)

        else:
            break

    return response


def _method(name):
    """create request call bound to a method"""

    async def inner(url, *args, **kwargs):
        return await call(url, *args, method=name, **kwargs)

    return inner


call.get = _method("GET")
call.post = _method("POST")
call.put = _method("PUT")
call.patch = _method("PATCH")
call.delete = _method("DELETE")


class _URL:  # pylint: disable=too-few-public-methods
    """url parser"""

    def __init__(self, url):
        parsed = urlparse(url)
        self.is_ssl = parsed.scheme == "https"
        if ":" in parsed.netloc:
            self.host, self.port = parsed.netloc.split(":", 1)
            self.port = int(self.port)
        else:
            self.host = parsed.netloc
            self.port = 443 if self.is_ssl else 80
        self.resource = parsed.path + (f"?{parsed.query if parsed.query else ''}")
        self.path = parsed.path if parsed.path else "/"
        self.query = parsed.query
