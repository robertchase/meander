from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass
import logging
import ssl

from meander.connection import HTTPConnection
from meander.router import Router
from meander.runner import Runnable, add_runnable


log = logging.getLogger(__package__)


@dataclass
class Server(Runnable):
    name: str
    routes: dict
    port: int
    ssl_certfile: str = None
    ssl_keyfile: str = None

    def __post_init__(self):
        if self.ssl_certfile and not self.ssl_keyfile:
            raise AttributeError("ssl_keyfile not specified")
        if self.ssl_keyfile and not self.ssl_certfile:
            raise AttributeError("ssl_certfile not specified")

    async def start(self):
        log.info("starting server %s on port %d", self.name, self.port)

        context = None
        if self.ssl_certfile and self.ssl_keyfile:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(self.ssl_certfile, self.ssl_keyfile)

        return (await asyncio.start_server(
            HTTPConnection(self.name, Router(self.routes)),
            port=self.port,
            ssl=context)
        ).serve_forever()


def add_server(name, routes, port, ssl_certfile=None, ssl_keyfile=None):
    add_runnable(Server(name, routes, port, ssl_certfile, ssl_keyfile))
