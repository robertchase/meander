"""basic ping/pong example"""
import meander as web


web.add_server({"/ping": "pong"})
web.run()
