"""ping/pong using a function from another module"""
import logging

import meander as web


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__package__)


web.add_server({"/ping": "examples.function-ping.ping"})
web.run()
