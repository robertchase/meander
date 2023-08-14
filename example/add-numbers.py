"""GET /add with annotations"""
import logging

import meander as web


logging.basicConfig(level=logging.INFO)


def add(a: int, b: int):
    """return the addition of the two integer parameters"""
    return a + b


web.add_server({"/add": add})
web.run()
