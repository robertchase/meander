"""manage meander servers"""

import asyncio
from dataclasses import dataclass
import logging
import ssl

from meander.connection import Connection
from meander import router
from meander.runner import add_task


log = logging.getLogger(__package__)


@dataclass
class Server:
    """container for server attributes

    at meander.run, start is called
    at connection to port, __call__ is called (via asyncio.start_server)
    """

    name: str
    routes: dict | str
    port: int
    base_url: str = None
    ssl_certfile: str = None
    ssl_keyfile: str = None

    def __post_init__(self):
        if self.ssl_certfile and not self.ssl_keyfile:
            raise AttributeError("ssl_keyfile not specified")
        if self.ssl_keyfile and not self.ssl_certfile:
            raise AttributeError("ssl_certfile not specified")

        if self.routes is None:
            self.router = router.Router()
        else:
            self.router = router.from_config(self.routes, self.base_url)

    def add_route(self, resource, handler, method="GET", before=None, silent=False):
        if before and callable(before):
            before = [before]
        self.router.add(router.Route(
            handler, resource, method, before, silent, self.base_url))
        return self

    async def start(self):
        """setup and start server listening on port"""
        if self.name:
            log.info("starting server %s on port %d", self.name, self.port)
        else:
            log.info("starting server on port %d", self.port)

        context = None
        if self.ssl_certfile and self.ssl_keyfile:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(self.ssl_certfile, self.ssl_keyfile)

        return await (
            await asyncio.start_server(self, port=self.port, ssl=context)
        ).serve_forever()

    async def __call__(self, reader, writer):
        """called for each new connection to the port"""
        connection = Connection(reader, writer, self.router, self.name)
        await connection.handle()


def add_server(  # pylint: disable=too-many-arguments
    routes: str | None = None,
    name: str | None = None,
    port: int = 8080,
    base_url: str | None = None,
    ssl_certfile: str | None = None,
    ssl_keyfile: str | None = None,
) -> Server:
    """define and add a new server for meander to run"""
    server = Server(name, routes, port, base_url, ssl_certfile, ssl_keyfile)
    add_task(server.start)
    return server
