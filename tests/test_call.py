"""tests for one-shot http client"""

import asyncio
from unittest.mock import AsyncMock, patch, MagicMock


from meander.call import call, _URL
from meander.document import ClientDocument
from meander.formatter import HTTPFormat
from meander.retry_policy import RetryPolicy, FixedBackoff

# --- _URL tests ---


def test_url_http_default_port():
    """test _URL parses http scheme with default port 80"""
    url = _URL("http://example.com/path")
    assert url.host == "example.com"
    assert url.port == 80
    assert url.is_ssl is False
    assert url.path == "/path"


def test_url_https_default_port():
    """test _URL parses https scheme with default port 443"""
    url = _URL("https://example.com/path")
    assert url.host == "example.com"
    assert url.port == 443
    assert url.is_ssl is True


def test_url_custom_port():
    """test _URL parses custom port from netloc"""
    url = _URL("http://localhost:9090/api")
    assert url.host == "localhost"
    assert url.port == 9090


def test_url_path_and_query():
    """test _URL parses path and query string"""
    url = _URL("http://example.com/api/data?key=val&foo=bar")
    assert url.path == "/api/data"
    assert url.query == "key=val&foo=bar"


def test_url_empty_path_defaults_to_slash():
    """test _URL defaults path to / when none given"""
    url = _URL("http://example.com")
    assert url.path == "/"


def test_url_no_query():
    """test _URL with no query string"""
    url = _URL("http://example.com/ping")
    assert url.query == ""


# --- call() tests ---


def _mock_client_factory(response):
    """create a mock Client class that returns a preset response"""

    def factory(verbose=False):
        client = MagicMock()
        client.open = AsyncMock()
        client.write = MagicMock(return_value=HTTPFormat(is_response=False))
        client.read = AsyncMock(return_value=response)
        client.close = AsyncMock()
        return client

    return factory


def _make_response(code=200, message="OK", headers=None):
    """create a ClientDocument with preset status"""
    doc = ClientDocument()
    doc.http_status_code = code
    doc.http_status_message = message
    doc.http_headers = headers or {}
    doc.http_content = b""
    return doc


def test_call_basic_get():
    """test call makes a GET request and returns response"""

    response = _make_response(200, "OK")

    async def test():
        with patch("meander.call.Client", _mock_client_factory(response)):
            result = await call("http://example.com/ping")
            assert result.http_status_code == 200
            assert result.request is not None

    asyncio.run(test())


def test_call_passes_method():
    """test call passes the method parameter to client.write"""
    response = _make_response(200, "OK")
    clients = []

    def factory(verbose=False):
        client = MagicMock()
        client.open = AsyncMock()
        client.write = MagicMock(return_value=HTTPFormat(is_response=False))
        client.read = AsyncMock(return_value=response)
        client.close = AsyncMock()
        clients.append(client)
        return client

    async def test():
        with patch("meander.call.Client", factory):
            await call("http://example.com/data", method="POST")
            assert clients[0].write.call_args.kwargs["method"] == "POST"

    asyncio.run(test())


def test_call_passes_bearer():
    """test call passes bearer token to client.write"""
    response = _make_response(200, "OK")
    clients = []

    def factory(verbose=False):
        client = MagicMock()
        client.open = AsyncMock()
        client.write = MagicMock(return_value=HTTPFormat(is_response=False))
        client.read = AsyncMock(return_value=response)
        client.close = AsyncMock()
        clients.append(client)
        return client

    async def test():
        with patch("meander.call.Client", factory):
            await call("http://example.com/api", bearer="tok123")
            assert clients[0].write.call_args.kwargs["bearer"] == "tok123"

    asyncio.run(test())


def test_call_follows_301_redirect():
    """test call follows 301 redirect to new host"""
    redirect_response = _make_response(
        301, "Moved", headers={"location": "http://new-host.com/ping"}
    )
    final_response = _make_response(200, "OK")
    call_count = 0

    def factory(verbose=False):
        nonlocal call_count
        client = MagicMock()
        client.open = AsyncMock()
        client.write = MagicMock(return_value=HTTPFormat(is_response=False))
        call_count += 1
        if call_count == 1:
            client.read = AsyncMock(return_value=redirect_response)
        else:
            client.read = AsyncMock(return_value=final_response)
        client.close = AsyncMock()
        return client

    async def test():
        with patch("meander.call.Client", factory):
            result = await call("http://example.com/ping")
            assert result.http_status_code == 200
            assert call_count == 2

    asyncio.run(test())


def test_call_follows_302_redirect():
    """test call follows 302 redirect to new host"""
    redirect_response = _make_response(
        302, "Found", headers={"location": "https://secure.com/login"}
    )
    final_response = _make_response(200, "OK")
    call_count = 0

    def factory(verbose=False):
        nonlocal call_count
        client = MagicMock()
        client.open = AsyncMock()
        client.write = MagicMock(return_value=HTTPFormat(is_response=False))
        call_count += 1
        if call_count == 1:
            client.read = AsyncMock(return_value=redirect_response)
        else:
            client.read = AsyncMock(return_value=final_response)
        client.close = AsyncMock()
        return client

    async def test():
        with patch("meander.call.Client", factory):
            result = await call("http://example.com/login")
            assert result.http_status_code == 200

    asyncio.run(test())


def test_call_no_redirect_without_location():
    """test call does not redirect when location header is missing"""
    response = _make_response(301, "Moved", headers={})

    async def test():
        with patch("meander.call.Client", _mock_client_factory(response)):
            result = await call("http://example.com/old")
            assert result.http_status_code == 301

    asyncio.run(test())


def test_call_retry_true_creates_default_policy():
    """test call with retry=True uses a default RetryPolicy"""
    response = _make_response(200, "OK")

    async def test():
        with patch("meander.call.Client", _mock_client_factory(response)):
            result = await call("http://example.com/ping", retry=True)
            assert result.http_status_code == 200

    asyncio.run(test())


def test_call_retry_retries_on_503():
    """test call retries on 503 with retry policy"""
    error_response = _make_response(503, "Service Unavailable")
    ok_response = _make_response(200, "OK")
    call_count = 0

    def factory(verbose=False):
        nonlocal call_count
        client = MagicMock()
        client.open = AsyncMock()
        client.write = MagicMock(return_value=HTTPFormat(is_response=False))
        call_count += 1
        if call_count == 1:
            client.read = AsyncMock(return_value=error_response)
        else:
            client.read = AsyncMock(return_value=ok_response)
        client.close = AsyncMock()
        return client

    async def test():
        policy = RetryPolicy(backoff=FixedBackoff(max_retry=3, initial_delay_ms=1))
        with patch("meander.call.Client", factory):
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                result = await call("http://example.com/api", retry=policy)
                assert result.http_status_code == 200
                assert call_count == 2
                mock_sleep.assert_called_once()

    asyncio.run(test())


def test_call_retry_stops_after_max():
    """test call stops retrying after policy max retries"""
    error_response = _make_response(503, "Service Unavailable")
    call_count = 0

    def factory(verbose=False):
        nonlocal call_count
        client = MagicMock()
        client.open = AsyncMock()
        client.write = MagicMock(return_value=HTTPFormat(is_response=False))
        call_count += 1
        client.read = AsyncMock(return_value=error_response)
        client.close = AsyncMock()
        return client

    async def test():
        policy = RetryPolicy(backoff=FixedBackoff(max_retry=2, initial_delay_ms=1))
        with patch("meander.call.Client", factory):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await call("http://example.com/api", retry=policy)
                assert result.http_status_code == 503
                assert call_count == 3  # initial + 2 retries

    asyncio.run(test())


def test_call_no_retry_on_200():
    """test call does not retry on success status"""
    response = _make_response(200, "OK")

    async def test():
        policy = RetryPolicy(backoff=FixedBackoff(max_retry=3, initial_delay_ms=1))
        with patch("meander.call.Client", _mock_client_factory(response)):
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                result = await call("http://example.com/api", retry=policy)
                assert result.http_status_code == 200
                mock_sleep.assert_not_called()

    asyncio.run(test())


def test_call_opens_ssl_for_https():
    """test call opens ssl connection for https urls"""
    response = _make_response(200, "OK")
    clients = []

    def factory(verbose=False):
        client = MagicMock()
        client.open = AsyncMock()
        client.write = MagicMock(return_value=HTTPFormat(is_response=False))
        client.read = AsyncMock(return_value=response)
        client.close = AsyncMock()
        clients.append(client)
        return client

    async def test():
        with patch("meander.call.Client", factory):
            await call("https://secure.example.com/api")
            clients[0].open.assert_called_once_with(
                "secure.example.com", 443, is_ssl=True
            )

    asyncio.run(test())


def test_call_closes_client():
    """test call closes the client after reading"""
    response = _make_response(200, "OK")
    clients = []

    def factory(verbose=False):
        client = MagicMock()
        client.open = AsyncMock()
        client.write = MagicMock(return_value=HTTPFormat(is_response=False))
        client.read = AsyncMock(return_value=response)
        client.close = AsyncMock()
        clients.append(client)
        return client

    async def test():
        with patch("meander.call.Client", factory):
            await call("http://example.com/ping")
            clients[0].close.assert_called_once()

    asyncio.run(test())


# --- _method() shortcut tests ---


def test_call_get_shortcut():
    """test call.get sends a GET request"""
    response = _make_response(200, "OK")
    clients = []

    def factory(verbose=False):
        client = MagicMock()
        client.open = AsyncMock()
        client.write = MagicMock(return_value=HTTPFormat(is_response=False))
        client.read = AsyncMock(return_value=response)
        client.close = AsyncMock()
        clients.append(client)
        return client

    async def test():
        with patch("meander.call.Client", factory):
            await call.get("http://example.com/data")
            assert clients[0].write.call_args.kwargs["method"] == "GET"

    asyncio.run(test())


def test_call_post_shortcut():
    """test call.post sends a POST request"""
    response = _make_response(200, "OK")
    clients = []

    def factory(verbose=False):
        client = MagicMock()
        client.open = AsyncMock()
        client.write = MagicMock(return_value=HTTPFormat(is_response=False))
        client.read = AsyncMock(return_value=response)
        client.close = AsyncMock()
        clients.append(client)
        return client

    async def test():
        with patch("meander.call.Client", factory):
            await call.post("http://example.com/data")
            assert clients[0].write.call_args.kwargs["method"] == "POST"

    asyncio.run(test())


def test_call_delete_shortcut():
    """test call.delete sends a DELETE request"""
    response = _make_response(200, "OK")
    clients = []

    def factory(verbose=False):
        client = MagicMock()
        client.open = AsyncMock()
        client.write = MagicMock(return_value=HTTPFormat(is_response=False))
        client.read = AsyncMock(return_value=response)
        client.close = AsyncMock()
        clients.append(client)
        return client

    async def test():
        with patch("meander.call.Client", factory):
            await call.delete("http://example.com/item/1")
            assert clients[0].write.call_args.kwargs["method"] == "DELETE"

    asyncio.run(test())
