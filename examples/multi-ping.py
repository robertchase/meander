"""make an call to another server"""
import logging

import meander as web


logging.basicConfig(level=logging.DEBUG)


SECONDARY = 12345


async def pingping():
    result = await web.call(f"http://localhost:{SECONDARY}/ping", verbose=True)
    return result.content


web.add_server(name="main").add_route("/ping", pingping)
web.add_server(name="secondary", port=SECONDARY).add_route("/ping", "pong")
web.run()
