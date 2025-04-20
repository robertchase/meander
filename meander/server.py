"""manage meander servers"""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
import logging
import io
import ssl

from meander.connection import Connection
from meander import router
from meander import runner


log = logging.getLogger(__package__)


@dataclass
class Server:
    """Container for server attributes.

    This is meant to be called from add_server, which adds the server to
    the runner module. At meander.run, start is called. At each connection to
    the port, __call__ is called (via asyncio.start_server)

    If you want to manage async Tasks on your own (in other words, not use
    the runner module), then create a Server, and call the start method, which
    returns a coroutine that can be handed to asyncio.create_task.
    """

    port: int
    name: str | None = None
    routes: str | io.IOBase | None = None
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
            self.router = router.load(self.routes, self.base_url)

    def add_route(
        self,
        resource: str,
        handler: str | Callable,
        method: str = "GET",
        before: Callable | list[Callable] | None = None,
        silent: bool = False,
    ):
        """Add a route to the server.

        resource - regex for matching HTTP request's resource
        handler - a callable to execute on match
                  or a dot-delimited path to an callable to be loaded
                  or a simple string (no imbedded dot character) to be returned
        method - the method match and HTTP request's method (eg, "POST")
        before - a callable, or list of callables, to run before calling the
                 handler
        silent - a flag to control connection logging

        This route will be evaluated for a match against an incoming HTTP
        request after any other routes that have already been added.
        """
        if before and callable(before):
            before = [before]
        self.router.add(
            router.Route(handler, resource, method, before, silent, self.base_url)
        )
        return self

    async def start(self):
        """Setup and start server listening on port."""
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
        """Called for each new connection to the port."""
        connection = Connection(reader, writer, self.router, self.name)
        await connection.handle()


def add_server(  # pylint: disable=too-many-arguments
    routes: str | io.IOBase | None = None,
    name: str | None = None,
    port: int = 8080,
    base_url: str | None = None,
    ssl_certfile: str | None = None,
    ssl_keyfile: str | None = None,
) -> Server:
    """Define and add a new server for meander to run."""
    server = Server(port, name, routes, base_url, ssl_certfile, ssl_keyfile)
    runner.add_task(server.start)
    return server
