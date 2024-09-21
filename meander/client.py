"""http client"""

import asyncio
from dataclasses import dataclass
import logging

from meander.parser import HTTPReader
from meander.formatter import HTTPFormat


log = logging.getLogger(__name__)


@dataclass
class Client:
    """async http client"""

    verbose: bool = False

    async def open(self, host, port, is_ssl=False):
        """open a connection to host/port"""
        # pylint: disable=attribute-defined-outside-init
        self.host = host
        reader, self.writer = await asyncio.open_connection(host, port, ssl=is_ssl)
        self.reader = HTTPReader(reader, is_server=False)

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
        """write an HTTP document to the writer"""
        if bearer:
            if not headers:
                headers = {}
            headers["Authorization"] = f"Bearer {bearer}"

        payload = HTTPFormat(
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

        return payload

    async def read(self, timeout=60, active_timeout=5, max_read_size=5000):
        """read response from socket"""
        self.reader.timeout = timeout
        self.reader.active_timeout = active_timeout
        self.reader.max_read_size = max_read_size

        result = await self.reader.read_document()

        if self.verbose:
            log.debug("%s %s", result.http_status_code, result.http_status_message)
            log.debug(result.http_headers)
            log.debug(result.http_content)

        return result

    async def close(self):
        """close the writer"""
        self.writer.close()
        await self.writer.wait_closed()
