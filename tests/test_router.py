"""test for router DSL"""
import io

import pytest

from meander import router
from tests import before as test_before


@pytest.mark.parametrize(
    "data, resource, method, args, silent, before",
    (
        ("""
            ROUTE /ping
            HANDLER pong
         """, "/ping", "GET", (), False, []),
        ("""
            ROUTE /ping
            HANDLER pong
            SILENT
         """, "/ping", "GET", (), True, []),
        ("""
            ROUTE /ping
            METHOD POST
            HANDLER pong
         """, "/ping", "POST", (), False, []),
        ("""
            ROUTE /ping/(\\d+)
            METHOD POST
            HANDLER pong
         """, "/ping/123", "POST", ('123',), False, []),
        ("""
            ROUTE /ping
            METHOD POST
            BEFORE tests.before.mock_before
            HANDLER pong
         """, "/ping", "POST", (), False, [test_before.mock_before]),
    ),
)
def test_endpoint(data, resource, method, args, silent, before):
    rtr = router.load(io.StringIO(data))
    assert len(rtr.routes) == 1
    route = rtr.routes[0]
    endpoint = route.match(resource, method)
    assert endpoint
    assert endpoint.args == args
    assert endpoint.silent is silent
    assert endpoint.before == before


@pytest.mark.parametrize(
    "resource, method",
    (
        ("/ping", "POST"),
        ("/ping/whatever", "GET"),
        ("/whatever/ping", "GET"),
        ("/ping/(\\d+)", "GET"),
    ),
)
def test_no_match(resource, method):
    rtr = router.load(io.StringIO("""
        ROUTE /ping
        HANDLER pong
    """))
    route = rtr.routes[0]
    assert route.match(resource, method) is None


def test_multiple_routes():
    rtr = router.load(io.StringIO("""
        ROUTE /ping
        HANDLER pong
        ROUTE /pong
        METHOD PUT
        HANDLER ping
    """))
    assert len(rtr.routes) == 2
    endpoint = rtr("/ping", "GET")
    assert endpoint
    assert endpoint.handler() == "pong"
    endpoint = rtr("/pong", "PUT")
    assert endpoint
    assert endpoint.handler() == "ping"


def test_multiple_methods():
    rtr = router.load(io.StringIO("""
        ROUTE /ping
        HANDLER pong
        METHOD PUT
        HANDLER put-pong
    """))
    assert len(rtr.routes) == 2
    endpoint = rtr("/ping", "GET")
    assert endpoint
    assert endpoint.handler() == "pong"
    endpoint = rtr("/ping", "PUT")
    assert endpoint
    assert endpoint.handler() == "put-pong"


def test_route_not_found():
    with pytest.raises(router.RouteNotDefinedError):
        router.load(io.StringIO("""
            HANLDER pong
        """))


def test_handler_not_defined():
    with pytest.raises(router.HandlerNotDefinedError):
        router.load(io.StringIO("""
            ROUTE /ping
        """))


def test_no_parameters_expected():
    with pytest.raises(router.NoParametersExpectedError):
        router.load(io.StringIO("""
            ROUTE /ping
            SILENT foo
        """))


def test_one_parameter_expected():
    with pytest.raises(router.OneParameterExpectedError):
        router.load(io.StringIO("""
            ROUTE /ping pong
        """))


def test_duplicate_directive():
    with pytest.raises(router.DuplicateDirectiveError):
        router.load(io.StringIO("""
            ROUTE /ping
            SILENT
            SILENT
        """))


def test_unexpected_directive():
    with pytest.raises(router.UnexpectedDirectiveError):
        router.load(io.StringIO("""
            ROUTE /ping
            FOO
        """))
