# CORS

CORS (Cross-Origin Resource Sharing) controls which web pages can make requests to your API from a browser. When a page at `app.example.com` calls your API at `api.example.com`, the browser blocks it unless your API responds with the right `Access-Control-*` headers.

The `meander.cors` module provides two factory functions that handle this.

## cors_after

Returns an `after` hook that adds CORS headers to responses. Attach it to any route that needs to accept cross-origin requests.

```python
from meander.cors import cors_after

server.add_route("/api/data", get_data, after=cors_after())
```

Parameters:

- **origins** — list of allowed origins, default `["*"]` (any origin). When `"*"` is in the list, the `Access-Control-Allow-Origin` header is set to `"*"`. Otherwise, the request's `Origin` header is checked against the list and echoed back if it matches.
- **methods** — list of allowed HTTP methods, default `["GET", "POST", "PUT", "DELETE"]`
- **headers** — list of allowed request headers, default `["Content-Type", "Authorization"]`

If the request has no `Origin` header, or the origin doesn't match, no CORS headers are added.

```python
# restrict to specific origins
after = cors_after(
    origins=["https://myapp.com", "https://staging.myapp.com"],
    methods=["GET", "POST"],
    headers=["Content-Type", "Authorization", "X-Request-Id"],
)
server.add_route("/api/users", get_users, after=after)
```

## cors_preflight

Returns a handler for `OPTIONS` preflight requests. Browsers send these before certain cross-origin requests to check what's allowed.

```python
from meander.cors import cors_preflight

server.add_route("/api/data", cors_preflight(), method="OPTIONS")
```

Parameters:

- **origins** — same as `cors_after`
- **methods** — same as `cors_after`
- **headers** — same as `cors_after`
- **max_age** — seconds the browser can cache the preflight result, default `86400` (24 hours)

The handler returns a `204 No Content` response with the appropriate CORS headers.

## Full example

```python
import meander
from meander.cors import cors_after, cors_preflight

def get_items():
    return [{"id": 1, "name": "widget"}]

def create_item(name):
    return {"id": 2, "name": name}

cors = cors_after(origins=["https://myapp.com"])
preflight = cors_preflight(origins=["https://myapp.com"])

server = meander.add_server(port=8080)
server.add_route("/api/items", get_items, after=cors)
server.add_route("/api/items", create_item, method="POST", after=cors)
server.add_route("/api/items", preflight, method="OPTIONS")

meander.run()
```

## Route config files

CORS hooks can also be used in `.routes` files via dot-delimited paths:

```
ROUTE /api/items
    METHOD GET
        HANDLER api.items.get_items
        AFTER myapp.cors.after_hook

    METHOD POST
        HANDLER api.items.create_item
        AFTER myapp.cors.after_hook

    METHOD OPTIONS
        HANDLER myapp.cors.preflight_handler
```

Where `myapp/cors.py` creates and exposes the hook instances:

```python
from meander.cors import cors_after, cors_preflight

after_hook = cors_after(origins=["https://myapp.com"])
preflight_handler = cors_preflight(origins=["https://myapp.com"])
```
