"""make an call to another server"""
import logging

import meander as web


logging.basicConfig(level=logging.DEBUG)


SECONDARY = 12345


async def pingping():
    result = await web.call(f"http://localhost:{SECONDARY}/ping", verbose=True)
    return result.content


web.add_server({
    "/ping": pingping,
}, name="main")


web.add_server({
    "/ping": "pong",
}, port=SECONDARY, name="secondary")

web.run()
