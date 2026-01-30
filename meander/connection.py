"""wrap tcp socket with HTTP logic"""

import asyncio
import itertools
import logging
import time

from meander import annotate
from meander import exception
from meander.parser import HTTPReader
from meander.parser import parse
from meander.response import Response


log = logging.getLogger(__package__)


connection_sequence = itertools.count(1)
request_sequence = itertools.count(1)


class Connection:
    """handle requests arriving on an HTTP connection"""

    def __init__(self, reader, writer, router, name=None):
        self.cid = next(connection_sequence)
        self.reader = HTTPReader(reader)
        self.writer = writer
        self.router = router

        self.silent = False
        self.message = None

        peerhost, peerport = self.writer.get_extra_info("peername")[:2]
        self.open_msg = f"open server={name} " if name else ""
        self.open_msg += f"socket={peerhost}:{peerport} cid={self.cid}"

    async def handle(self):
        """handle new connection"""

        t_start = time.perf_counter()
        try:
            while await self.next_request():
                pass
        finally:
            if not self.silent:
                elapsed = f"t={time.perf_counter() - t_start:.6f}"
                log.info("close cid=%s %s", self.cid, elapsed)
            try:
                await self.writer.drain()
                self.writer.close()
            except ConnectionResetError:
                pass

    async def next_request(self) -> bool:
        """get and handle the next request arriving on the connection"""
        self.message = None
        reason_code = 200
        r_start = time.perf_counter()
        try:
            if request := await parse(self.reader):
                r_start = time.perf_counter()
                return await self.handle_request(request)
        except (
            exception.DuplicateAttributeError,
            exception.ExtraAttributeError,
            exception.PayloadValueError,
            exception.RequiredAttributeError,
        ) as err:
            reason_code = 400
            result = Response(str(err), 400, "Bad Request")
            self.writer.write(result.serial())
        except asyncio.exceptions.TimeoutError:
            log.info("timeout cid=%s", self.cid)
        except exception.HTTPException as exc:
            reason_code = exc.code
            result = self.on_http_exception(exc)
            self.writer.write(result.serial())
        except ConnectionResetError:
            log.info("connection cid=%s reset by peer", self.cid)
        except Exception:  # pylint: disable=broad-exception-caught
            log.exception("exception: cid=%s", self.cid)
            reason_code = 500
            result = self.on_exception()
            self.writer.write(result.serial())
        finally:
            if not self.silent:
                if self.open_msg:
                    log.info(self.open_msg)
                if self.message:
                    self.message += (
                        f" status={reason_code} t={time.perf_counter() - r_start:f}"
                    )
                    log.info(self.message)

    async def handle_request(self, request) -> bool:
        """handle a single request"""
        rid = next(request_sequence)
        request.id = rid
        request.connection_id = self.cid
        self.message = (
            f"request cid={self.cid}"
            f" rid={rid} method={request.http_method}"
            f" resource={request.http_resource}"
        )
        if route := self.router(request.http_resource, request.http_method):
            self.silent = route.silent
            if self.open_msg:
                if not self.silent:
                    log.info(self.open_msg)
                self.open_msg = None
            request.args = route.args

            for before in route.before:
                result = before(request)
                if asyncio.iscoroutine(result):
                    await result

            result = annotate.call(route.handler, request)
            if asyncio.iscoroutine(result):
                result = await result

            if result is None:
                result = ""
            if not isinstance(result, Response):
                result = Response(result)
            self.writer.write(result.serial())
            return request.is_keep_alive

        raise exception.HTTPException(404, "Not Found")

    def on_http_exception(self, exc):
        """handle http exception response"""
        return Response(code=exc.code, message=exc.reason, content=exc.explanation)

    def on_exception(self):
        """handle general exception response"""
        return Response(code=500, message="Internal Server Error")
