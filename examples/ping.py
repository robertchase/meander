"""basic ping/pong example"""
import meander as web


web.add_server().add_route("/ping", "pong")
web.run()
