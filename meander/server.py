import asyncio
from dataclasses import dataclass
import logging

from meander.connection import HTTPConnection
from meander.router import Router


log = logging.getLogger(__package__)


servers = []


@dataclass
class Server:
    name: str
    routes: dict
    port: int

    async def start(self):
        log.info("starting server %s on port %d", self.name, self.port)
        return (await asyncio.start_server(
            HTTPConnection(self.name, Router(self.routes)), port=self.port)
        ).serve_forever()


def add_server(name, routes, port):
    servers.append(Server(name, routes, port))


def run():

    async def _run():
        await asyncio.gather(
            *[await server.start() for server in servers]
        )

    asyncio.run(_run())
