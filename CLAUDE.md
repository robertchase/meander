# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Meander is a tiny async Python web framework (Python 3.12+) that automatically exposes Python functions as HTTP API endpoints. The core philosophy is separation of API wiring from code construction—functions are written normally without decorators, then wired to HTTP endpoints where parameters are automatically extracted from requests based on function annotations.

## Common Commands

```bash
PYTHONPATH=. .venv/bin/pytest tests          # Run all tests
.venv/bin/ruff check meander tests           # Run ruff linter
.venv/bin/black meander tests                # Format code with black
```

Run a single test:
```bash
PYTHONPATH=. .venv/bin/pytest tests/test_annotate.py -v
PYTHONPATH=. .venv/bin/pytest tests/test_annotate.py::test_function_name -v
```

## Architecture

### Request Flow

1. `runner.py` manages the async event loop and starts servers
2. `server.py` creates Server instances that own a Router
3. `connection.py` handles HTTP connections, parses requests, and dispatches to handlers
4. `router.py` matches URL patterns (regex) + HTTP methods to Route definitions
5. `annotate.py` inspects handler function signatures, extracts parameters from requests, converts types, and invokes the handler
6. `response.py` / `formatter.py` serialize results back to HTTP

### Key Modules

- **annotate.py**: Core parameter extraction logic. `get_params()` (cached) inspects function signatures; `call()` extracts values from requests, converts types, and invokes handlers
- **router.py**: `Router` class matches requests to `Route` objects. Routes use regex patterns. `load()` parses `.routes` config files
- **connection.py**: `Connection` class handles request lifecycle, logging (cid/rid tracking), error handling, and keep-alive
- **types_.py**: Type converters (`boolean`, `integer`, `String`) and special markers (`ConnectionId`, `Ignore`)
- **call.py**: HTTP client for outbound requests with retry support
- **parser.py** / **formatter.py**: HTTP protocol parsing and serialization

### Special Parameter Types

Functions can use these annotations for automatic injection:
- `Request` (aliased from `ServerDocument`): Inject the full HTTP request object
- `ConnectionId`: Inject connection/request ID string
- `Ignore`: Skip parameter extraction for this argument
