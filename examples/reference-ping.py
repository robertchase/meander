"""ping/pong using a function from another module"""
import logging

import meander as web


logging.basicConfig(level=logging.INFO)


web.add_server({"/ping": "examples.function-ping.ping"})
web.run()
