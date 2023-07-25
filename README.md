# meander
tiny asnyc web

# examples
## basic operation

```
import meander as web

web.add_server({"/ping": "pong"})
web.run()
```

This code creates and runs an `HTTP` server listening on port `8080` that responds to `GET` requests for `/ping` with the string "pong". This result is wrapped in a `text/plain` response.

If we saved the code in a file named `my-server.py`, then running it is a simple as this:

```
python3 my-server.py
```
Note: *`meander` is in the PYTHONPATH*.<br>The server will run until stopped from the terminal with `CTRL-C`.

To talk to the server, use `curl` in another terminal:

```
curl -v localhost:8080/ping
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
pong
```
## logging
Log messages are automatically produced by the server using python's `logging` library.

```
import logging
import meander as web

logging.basicConfig(level=logging.INFO)

web.add_server({"/ping": "pong"})
web.run()
```
Running the server now produces log messages.

```
python3 my-server.py
INFO:meander:starting server on port 8080
```

Each `HTTP` connection and request is also logged, including a unique id (cid) for each connection and request (rid), and timing information.

```
INFO:meander:open socket=127.0.0.1:55198 cid=1
INFO:meander:request cid=1 rid=1 method=GET resource=/ping status=200 t=0.000140
INFO:meander:close cid=1 t=0.000760
```

## beyond the basics

Responding to a `url` with a simple string is not widely useful.
We'll look at some additional ways to handle client requests. 
### local function

A local or imported function is registered by using the function name:

```
def echo(request):
    return request.content
    
web.add_server({
    "/ping": "pong",
    "/echo": echo,
)}
```

A call to the `echo` endpoint produces an empty result, because no `content` was supplied.

```
curl -v localhost:8080/echo
* Connected to localhost (127.0.0.1) port 8080 (#0)
> GET /echo HTTP/1.1
> Host: localhost:8080
> User-Agent: curl/7.88.1
> Accept: */*
>
< HTTP/1.1 200 OK
< Date: Sat, 22 Jul 2023 09:00:11 EDT
< Content-Length: 0
```

A `GET` method does not support content, but it does support a `query string`. Any `query string` parameters will be converted into a `dict` and stored in the `request.content` attribute. Since the `echo` handler returns the `content`, the result will contain the `dict` as `application/json` content.

```
curl -v localhost:8080/echo\?this=is\&a=test
* Connected to localhost (127.0.0.1) port 8080 (#0)
> GET /echo?this=is&a=test HTTP/1.1
> Host: localhost:8080
> User-Agent: curl/7.88.1
> Accept: */*
>
< HTTP/1.1 200 OK
< Content-Type: application/json; charset=utf-8
< Date: Sat, 22 Jul 2023 09:13:15 EDT
< Content-Length: 27
<
{"this": "is", "a": "test"}
```

### supporting other methods

Let's add a `GET` and a `PUT` to the `echo` endpoint. Both methods use the same function.

```
web.add_server({
    "/ping": "pong",
    "/echo": {
        "GET": echo,
        "PUT": echo,
    },
)}
```

The `GET` call will work the same. What happens with `PUT`? We'll send some simple text data to the endpoint and see.

```
curl -v localhost:8080/echo -XPUT --data "this is a test" -H "content-type: text/plain"
* Connected to localhost (127.0.0.1) port 8080 (#0)
> PUT /echo HTTP/1.1
> Host: localhost:8080
> User-Agent: curl/7.88.1
> Accept: */*
> content-type: text/plain
> Content-Length: 14
>
< HTTP/1.1 200 OK
< Content-Type: text/plain; charset=utf-8
< Date: Sat, 22 Jul 2023 09:40:13 EDT
< Content-Length: 14
<
this is a test
```

The data we sent was supplied in the `request.content` attribute. Although there are other attributes that show specifically what arrived in the `query string` or in the `http_content` area, the request attempts to coerce the input data (with specific attention to `form`, `json`, and `query string` data) into this single attribute, no matter the `HTTP` method used.

Here is a `PUT` with `form` data:

```
curl -v localhost:8080/echo -XPUT -d a=1 -d b=2
* Connected to localhost (127.0.0.1) port 8080 (#0)
> PUT /echo HTTP/1.1
> Host: localhost:8080
> User-Agent: curl/7.88.1
> Accept: */*
> Content-Length: 7
> Content-Type: application/x-www-form-urlencoded
>
< HTTP/1.1 200 OK
< Content-Type: application/json; charset=utf-8
< Date: Sat, 22 Jul 2023 09:47:23 EDT
< Content-Length: 20
<
{"a": "1", "b": "2"}
```

The `form` data is converted into a `dict` and stored in `request.content`. When the content is returned by the `echo` handler, it is converted to `json`.

### payload