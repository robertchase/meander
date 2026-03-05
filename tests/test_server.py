"""tests for server configuration and routing setup"""

import io

import pytest

from meander.server import Server, add_server
from meander import runner


def test_server_creates_empty_router():
    """test server with no routes creates an empty router"""
    server = Server(port=8080)
    assert server.router is not None
    assert server.router.routes == []


def test_server_with_name():
    """test server stores name"""
    server = Server(port=8080, name="test-server")
    assert server.name == "test-server"


def test_server_ssl_missing_keyfile():
    """test server raises when ssl_certfile given without ssl_keyfile"""
    with pytest.raises(AttributeError, match="ssl_keyfile not specified"):
        Server(port=443, ssl_certfile="cert.pem")


def test_server_ssl_missing_certfile():
    """test server raises when ssl_keyfile given without ssl_certfile"""
    with pytest.raises(AttributeError, match="ssl_certfile not specified"):
        Server(port=443, ssl_keyfile="key.pem")


def test_server_ssl_both_specified():
    """test server accepts both ssl_certfile and ssl_keyfile"""
    server = Server(port=443, ssl_certfile="cert.pem", ssl_keyfile="key.pem")
    assert server.ssl_certfile == "cert.pem"
    assert server.ssl_keyfile == "key.pem"


def test_server_loads_routes_from_stream():
    """test server loads routes from an io stream"""
    config = io.StringIO("ROUTE /ping\nHANDLER pong\n")
    server = Server(port=8080, routes=config)
    endpoint = server.router("/ping", "GET")
    assert endpoint is not None
    assert endpoint.handler() == "pong"


def test_server_loads_routes_with_base_url():
    """test server applies base_url to routes from stream"""
    config = io.StringIO("ROUTE /ping\nHANDLER pong\n")
    server = Server(port=8080, routes=config, base_url="/api")
    assert server.router("/api/ping", "GET") is not None
    assert server.router("/ping", "GET") is None


def test_add_route_callable():
    """test add_route with a callable handler"""

    def handler():
        return "ok"

    server = Server(port=8080)
    result = server.add_route("/test", handler)

    assert result is server  # returns self for chaining
    endpoint = server.router("/test", "GET")
    assert endpoint is not None
    assert endpoint.handler() == "ok"


def test_add_route_string_handler():
    """test add_route with a simple string handler"""
    server = Server(port=8080)
    server.add_route("/health", "healthy")

    endpoint = server.router("/health", "GET")
    assert endpoint is not None
    assert endpoint.handler() == "healthy"


def test_add_route_method():
    """test add_route with a specific method"""

    def handler():
        return "created"

    server = Server(port=8080)
    server.add_route("/items", handler, method="POST")

    assert server.router("/items", "POST") is not None
    assert server.router("/items", "GET") is None


def test_add_route_silent():
    """test add_route with silent flag"""

    def handler():
        return "ok"

    server = Server(port=8080)
    server.add_route("/health", handler, silent=True)

    endpoint = server.router("/health", "GET")
    assert endpoint.silent is True


def test_add_route_with_before_callable():
    """test add_route wraps a single before callable in a list"""

    def my_before(request):
        pass

    def handler():
        return "ok"

    server = Server(port=8080)
    server.add_route("/test", handler, before=my_before)

    endpoint = server.router("/test", "GET")
    assert len(endpoint.before) == 1
    assert endpoint.before[0] is my_before


def test_add_route_with_before_list():
    """test add_route accepts a list of before callables"""

    def before_1(request):
        pass

    def before_2(request):
        pass

    def handler():
        return "ok"

    server = Server(port=8080)
    server.add_route("/test", handler, before=[before_1, before_2])

    endpoint = server.router("/test", "GET")
    assert len(endpoint.before) == 2


def test_add_route_with_base_url():
    """test add_route applies server base_url"""
    server = Server(port=8080, base_url="/v1")
    server.add_route("/items", "list")

    assert server.router("/v1/items", "GET") is not None
    assert server.router("/items", "GET") is None


def test_add_route_chaining():
    """test add_route returns self for method chaining"""
    server = Server(port=8080)
    result = server.add_route("/a", "a").add_route("/b", "b").add_route("/c", "c")

    assert result is server
    assert server.router("/a", "GET") is not None
    assert server.router("/b", "GET") is not None
    assert server.router("/c", "GET") is not None


def test_add_server_creates_and_registers():
    """test add_server creates a Server and adds it to runner tasks"""
    original_tasks = runner.tasks.copy()
    try:
        runner.tasks.clear()
        server = add_server(port=9999, name="test")
        assert isinstance(server, Server)
        assert server.port == 9999
        assert server.name == "test"
        assert len(runner.tasks) == 1
    finally:
        runner.tasks[:] = original_tasks
