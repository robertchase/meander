"""manage meander servers"""
import asyncio
from dataclasses import dataclass
import logging
import ssl

from meander.connection import Connection
from meander.router import Router
from meander.runner import Runnable, add_runnable


log = logging.getLogger(__package__)


@dataclass
class Server(Runnable):
    """container for server attributes

    performs asyncio.start_server right before event loop start

    gets __call__'ed on each connection
    """

    name: str
    routes: dict
    port: int
    base_url: str = None
    ssl_certfile: str = None
    ssl_keyfile: str = None

    def __post_init__(self):
        if self.ssl_certfile and not self.ssl_keyfile:
            raise AttributeError("ssl_keyfile not specified")
        if self.ssl_keyfile and not self.ssl_certfile:
            raise AttributeError("ssl_certfile not specified")
        self.router = Router(self.routes, self.base_url)

    async def start(self):
        if self.name:
            log.info("starting server %s on port %d", self.name, self.port)
        else:
            log.info("starting server on port %d", self.port)

        context = None
        if self.ssl_certfile and self.ssl_keyfile:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(self.ssl_certfile, self.ssl_keyfile)

        return (
            await asyncio.start_server(self, port=self.port, ssl=context)
        ).serve_forever()

    async def __call__(self, reader, writer):
        connection = Connection(reader, writer, self.name, self.router)
        await connection.handle()


def add_server(  # pylint: disable=too-many-arguments
    routes: dict,
    name: str = None,
    port: int = 8080,
    base_url: str = None,
    ssl_certfile: str = None,
    ssl_keyfile: str = None,
) -> Server:
    """define and add a new server for meander to run"""
    server = Server(name, routes, port, base_url, ssl_certfile, ssl_keyfile)
    add_runnable(server)
    return server
