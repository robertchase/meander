"""GET /add"""
import logging

import meander as web


logging.basicConfig(level=logging.INFO)


def add(a, b):
    """return the addition of the two parameters"""
    return a + b


web.add_server().add_route("/add", add)
web.run()
