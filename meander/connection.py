from asyncio.exceptions import TimeoutError
from itertools import count
import logging
import time

from meander import exception
from meander.parser import HTTPReader
from meander.parser import parse
from meander.response import Response


log = logging.getLogger(__package__)


connection_sequence = count(1)
request_sequence = count(1)


class HTTPConnection:

    def __init__(self, name, router,
                 on_404=None,
                 on_500=None):
        self.name = name
        self.router = router
        self.on_404 = on_404
        self.on_500 = on_500

    async def __call__(self, reader, writer):
        reader = HTTPReader(reader)

        async def handle():
            nonlocal silent
            nonlocal open_msg
            message = None
            keep_alive = False
            try:
                if request := await parse(reader):
                    rid = next(request_sequence)
                    reason_code = 200
                    r_start = time.perf_counter()
                    message = (
                        f"request cid={cid}"
                        f" rid={rid} method={request.http_method}"
                        f" resource={request.http_resource}")
                    if route := self.router(request.http_resource,
                                            request.http_method):
                        silent = route.silent
                        if open_msg:
                            if not silent:
                                log.info(open_msg)
                            open_msg = None
                        request.args = route.args
                        request.connection_id = cid
                        request.id = rid
                        result = await route.handler(request)
                        if result is None:
                            result = ""
                        if not isinstance(result, Response):
                            result = Response(result)
                        writer.write(result.value)
                        keep_alive = request.is_keep_alive
                    else:
                        raise exception.HTTPException(404, "Not Found")
            except (exception.DuplicateAttributeError,
                    exception.ExtraAttributeError,
                    exception.PayloadValueError,
                    exception.RequiredAttributeError) as err:
                reason_code = 400
                writer.write(Response(str(err), 400, "Bad Request").value)
            except TimeoutError:
                keep_alive = False
                log.info(f"timeout {cid=}")
            except exception.HTTPException as exc:
                reason_code = exc.code
                if reason_code == 404 and self.on_404:
                    writer.write(Response(self.on_404()).value)
                else:
                    writer.write(
                        Response(code=exc.code, message=exc.reason,
                                 content=exc.explanation).value)
            except Exception:
                log.exception(f"exception: cid={cid}")
                reason_code = 500
                if self.on_500:
                    writer.write(Response(self.on_500()).value)
                else:
                    writer.write(Response(
                        code=500, message="Internal Server Error").value)
            finally:
                if not silent:
                    if open_msg:
                        log.info(open_msg)
                    if message:
                        message += (
                            f" status={reason_code}"
                            f" t={time.perf_counter() - r_start:f}")
                        log.info(message)
                return keep_alive

        try:
            silent = False
            t_start = time.perf_counter()
            peerhost, peerport = writer.get_extra_info("peername")[:2]
            cid = next(connection_sequence)
            open_msg = (
                f"open server={self.name}"
                f" socket={peerhost}:{peerport}"
                f" cid={cid}")
            while await handle():
                pass
        finally:
            if not silent:
                log.info(
                    f"close cid={cid}"
                    f" t={time.perf_counter() - t_start:.6f}")
            try:
                await writer.drain()
                writer.close()
            except ConnectionResetError:
                pass
