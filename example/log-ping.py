"""basic ping/pong with logging example"""
import logging

import meander as web


logging.basicConfig(level=logging.INFO)

web.add_server({"/ping": "pong"})
web.run()
