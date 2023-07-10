# meander
tiny asnyc web

# examples
## basic operation

```
import meander as web

async def ping(request: web.Request) -> str:
    return "pong"
    
web.add_server(
    "test-server",
    {"/ping": {"GET": ping}},
    12345)
web.run()
```

This code creates and runs an `HTTP` server listening on port `12345` that routes urls that point to `/ping` to the defined async `ping` function. The function returns the string "pong" which is wrapped in a `text/plain` response.

If we saved the code in a file named `my-server.py`, then running it is a simple as this:

```
python3 my-server.py
```
The server will run until stopped from the terminal with `CTRL-C`.

To talk to the server, use `curl` in another terminal:

```
curl -v localhost:12345/ping
  *   Trying 127.0.0.1:12345...
  * Connected to localhost (127.0.0.1) port 12345 (#0)
  > GET /ping HTTP/1.1
  > Host: localhost:12345
  > User-Agent: curl/7.88.1
  > Accept: */*
  >
  < HTTP/1.1 200 OK
  < Content-Type: text/plain; charset=utf-8
  < Date: Sat, 08 Jul 2023 09:01:37 EDT
  < Content-Length: 4
  <
  * Connection #0 to host localhost left intact
pong
```
## logging
Log messages are automatically produced by the server using the `logging` library.

```
import logging

import meander as web

logging.basicConfig(level=logging.DEBUG)

async def ping(request: web.Request) -> str:
    return "pong"
    
web.add_server(
    "test-server",
    {"/ping": {"GET": ping}},
    12345)
web.run()
```
Running the server now produces log messages. The first parameter to the `add_server`  method is used to identify the server.

```
python3 my-server.py
DEBUG:asyncio:Using selector: KqueueSelector
INFO:meander:starting server test-server on port 12345
```

Each `HTTP` connection and request is also logged, including a unique id (cid) for each connection and request (rid), and timing information.

```
INFO:meander:open server=test-server socket=127.0.0.1:55198 cid=1
INFO:meander:request cid=1 rid=1 method=GET resource=/ping status=200 t=0.000140
INFO:meander:close cid=1 t=0.000760
```

Asdf. 