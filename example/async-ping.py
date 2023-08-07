"""make an async call to another endpoint"""
import logging

import meander as web


logging.basicConfig(level=logging.INFO)


async def pingping():
    result = await web.call("http://localhost:8080/ping")
    return result.content


web.add_server({
    "/ping": "pong",
    "/pingping": pingping,
})
web.run()
