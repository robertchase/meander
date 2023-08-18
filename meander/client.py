"""http client"""
import asyncio
import logging

from meander.parser import HTTPReader
from meander.formatter import HTMLFormat


log = logging.getLogger(__name__)


class Client:
    """async http client"""

    def __init__(self, host, port, is_ssl=False, verbose=False):
        self.host = host
        self.port = port
        self.is_ssl = is_ssl
        self.verbose = verbose
        self.reader = None
        self.writer = None

    async def open(self):
        """open a connection to the host specified in the url"""
        self.reader, self.writer = await asyncio.open_connection(
            self.host, self.port, ssl=self.is_ssl
        )

    def write(  # pylint: disable=too-many-arguments
        self,
        method="GET",
        path="/",
        query_string="",
        content="",
        headers=None,
        content_type=None,
        charset="utf-8",
        compress=False,
        bearer=None,
        close=False,
    ):
        """write an HTTP document to the socket"""
        if bearer:
            if not headers:
                headers = {}
            headers["Authorization"] = f"Bearer {bearer}"

        payload = HTMLFormat(
            is_response=False,
            method=method,
            path=path,
            query=query_string,
            headers=headers,
            content=content,
            host=self.host,
            content_type=content_type,
            charset=charset,
            compress=compress,
            close=close,
        )
        self.writer.write(payload.serial())

        if self.verbose:
            log.debug(payload.serial())

    async def read(self, timeout=60, active_timeout=5, max_read_size=5000):
        """read response from socket"""
        http_reader = HTTPReader(
            self.reader,
            is_server=False,
            timeout=timeout,
            active_timeout=active_timeout,
            max_read_size=max_read_size,
        )

        result = await http_reader.read_document()

        if self.verbose:
            log.debug("%s %s", result.http_status_code, result.http_status_message)
            log.debug(result.http_headers)
            log.debug(result.http_content)

        return result

    async def close(self):
        """close the writer"""
        self.writer.close()
        await self.writer.wait_closed()
