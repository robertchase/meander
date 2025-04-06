"""GET /echo"""
import logging

import meander as web


logging.basicConfig(level=logging.INFO)


def echo(content):
    return content


web.add_server().add_route("echo", echo)
web.run()
