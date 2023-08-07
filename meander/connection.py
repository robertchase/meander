"""wrap tcp socket with HTTP logic"""
import asyncio
from itertools import count
import logging
import time

from meander import annotate
from meander import exception
from meander.parser import HTTPReader
from meander.parser import parse
from meander.response import Response


log = logging.getLogger(__package__)


connection_sequence = count(1)
request_sequence = count(1)


class HTTPConnection:  # pylint: disable=too-few-public-methods
    """handle requests arriving on an HTTP connection"""

    def __init__(self, name, router, on_404=None, on_500=None):
        self.name = name
        self.router = router
        self.on_404 = on_404
        self.on_500 = on_500

    async def __call__(self, reader, writer):
        # pylint: disable=too-many-statements
        reader = HTTPReader(reader)

        async def handle():  # pylint: disable=too-many-branches
            nonlocal silent
            nonlocal open_msg
            message = None
            keep_alive = False
            r_start = time.perf_counter()
            try:  # pylint: disable=too-many-nested-blocks
                if request := await parse(reader):
                    rid = next(request_sequence)
                    reason_code = 200
                    message = (
                        f"request cid={cid}"
                        f" rid={rid} method={request.http_method}"
                        f" resource={request.http_resource}"
                    )
                    if route := self.router(request.http_resource, request.http_method):
                        silent = route.silent
                        if open_msg:
                            if not silent:
                                log.info(open_msg)
                            open_msg = None
                        request.args = route.args
                        request.connection_id = cid
                        request.id = rid

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
                        writer.write(result.serial())
                        keep_alive = request.is_keep_alive
                    else:
                        raise exception.HTTPException(404, "Not Found")
            except (
                exception.DuplicateAttributeError,
                exception.ExtraAttributeError,
                exception.PayloadValueError,
                exception.RequiredAttributeError,
            ) as err:
                reason_code = 400
                result = Response(str(err), 400, "Bad Request")
                writer.write(result.serial())
            except asyncio.exceptions.TimeoutError:
                keep_alive = False
                log.info("timeout cid=%s", cid)
            except exception.HTTPException as exc:
                reason_code = exc.code
                if reason_code == 404 and self.on_404:
                    result = Response(self.on_404())
                else:
                    result = Response(
                        code=exc.code, message=exc.reason, content=exc.explanation
                    )
                writer.write(result.serial())
            except Exception:  # pylint: disable=broad-exception-caught
                log.exception("exception: cid=%s", cid)
                reason_code = 500
                if self.on_500:
                    result = Response(self.on_500())
                else:
                    result = Response(code=500, message="Internal Server Error")
                writer.write(result.serial())
            finally:
                if not silent:
                    if open_msg:
                        log.info(open_msg)
                    if message:
                        message += (
                            f" status={reason_code}"
                            f" t={time.perf_counter() - r_start:f}"
                        )
                        log.info(message)
            return keep_alive

        t_start = time.perf_counter()
        silent = False
        try:
            peerhost, peerport = writer.get_extra_info("peername")[:2]
            cid = next(connection_sequence)
            open_msg = f"open server={self.name} " if self.name else ""
            open_msg += f"socket={peerhost}:{peerport}" f" cid={cid}"
            while await handle():
                pass
        finally:
            if not silent:
                elapsed = f"t={time.perf_counter() - t_start:.6f}"
                log.info("close cid=%s %s", cid, elapsed)
            try:
                await writer.drain()
                writer.close()
            except ConnectionResetError:
                pass
