"""GET /add add or increment"""
import logging

import meander as web


logging.basicConfig(level=logging.INFO)


def add(a: int, b: int = 1):
    """add or increment"""
    return a + b


web.add_server().add_route("/add", add)
web.run()
