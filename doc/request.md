# Request

A `meander.Request` (`meander.document.ServerDocument`) is a container for a single `HTTP` document that arrives on an inbound `meander` connection.

If a handler function has a parameter with a `meander.Request` annotation, then the `Request` object will be explicitly passed in this parameter. There is no *secret* or *magic* way to access the `Request`. *Note that using a `Request` in a handler function makes that function dependent on `HTTP` (or an equivalent proxy/mock)&mdash;this goes against the grain of `meander` design principles. See "best practices" below*.

```
class ServerDocument:
    id: int
    connection_id: int
    
    http_method: str
    http_resource: str
    http_query_string: str
    http_query: dict
    http_headers: dict
    http_content_length: int
    http_charset: str
    http_encoding: str
    http_content_type: str
    http_content: bytes
    
    args: tuple
    content: None | dict | str | bytes
    is_keep_alive: bool    
```

### id and connection_id

Each connection to a `meander` server gets a unique integer `connection_id`;
each `HTTP` request arriving on a connection gets a unique integer `id`. The combination of these two values is unique across any execution of a python program using `meander` (no matter how many different `meander` servers are added). The ids will start over if the python executable is restarted.

A string of the form `f"con={request.connection_id} req={request.id}"` (useful for log messages) is available using the `web.ConnectionId` annotation. If this annotation is used, be sure to provide a default value (`None` is reasonable) that allows the function to run outside of `meander`, and make sure that any code using this value handles the default gracefully.

### http\_method, http\_resource, and http\_query\_string

These values are taken directly from the inbound `HTTP` request. The `method` and `resource` are used by `meander` to route the request to the proper handler function, and the `query_string` is parsed and made available through the `http_query` or `content` attributes.

### http\_query

`http_query` is a `dict` containing the parsed `http_query_string`. If `http_query_string` is empty, then `http_query` is an empty `dict`; otherwise, the key-value pairs in `http_query_string` become key-value pairs in `http_query`. An `HTTP` query string can contain multiple occurrences of a key; in this case, `http_query` will contain a list of each value associated with the key.

### http\_headers

`http_headers` is a `dict` containing each header record found in the inbound `HTTP` request. The key is the name of the header, forced to lower case&mdash;`HTTP` header names are case-insensitive.

### http\_content\_length, http\_content\_type, http\_charset, and http\_encoding 

These values are derived from the `HTTP` request's headers:

* `http_content_length` is derived from the `content-length` header
* `http_content_type` and `http_content_charset` are derived from the `content-type` header
* `http_encoding` is derived from the `content-encoding` header

### http\_content

`http_content` is a byte string containing the body of the inbound `HTTP` request.

### args

If any regex groups are defined in the *pattern* used in the *routes* argument to the `add_server` function, those groups will be added as the `args` attribute to the `Request` that matches the route. For instance, the route:

```
"/foo/([a-z]*)/(\d*)"
```

will match any `HTTP` resource that starts with "/foo/", followed by one or more lowercase letters, followed by "/", followed by one or more digits. The parenthesis around `[a-z]\*` and `\d*` will cause the values that match these two strings to be added as a tuple to the "args" attribute of the `Request`.

*Note*: Creating groups with parenthesis are standard syntax for the `python` `re` package. Refer to the `python` documentation for more detail.

### content

`content` is one of:

* the `http_query` value of a `GET` call
* the `json.loads` of the `http_content` of a `POST`, `PUT`, or `PATCH` call having `application/json` `http_content_type`
* a `dict` conversion of the `http_content` of a `POST`, `PUT`, or `PATCH` call having `application/x-www-form-urlencoded` `http_content_type`
* the decoded string value of the `http_content` of a `POST`, `PUT` or `PATCH` call having `text/plain` `http_content_type`
* the `http_content` of a `POST`, `PUT` or `PATCH` call not matching any of the above
* otherwise `None`

### is\_keep\_alive

`is_keep_alive` is a `bool` set to `True` if the `connection` header has the value "keep-alive".

## best practices

`meander` allows you connect "normal" python functions to the web. If a function expects a `Request` as a parameter, then it is no longer "normal", but is, instead, tied to to the web. This defeats a primary purpose of `meander`, namely, the separation of `HTTP` details and handler functions.

In order to avoid mixing your handler functions with `HTTP`, use one or more `before` functions when setting up the `routes` in `add_server`. Each `before` function is passed the `Request` object where web-specific logic can be executed *before the handler function is called*. Headers values can be checked, special payload handling can be performed, `args` and `content` can be manipulated&mdash;anything that would normally be processed in an `HTTP` handler can be performed in a `before` function, thereby, isolating the handler function from any awareness of `HTTP`. Think of a `before` function as a decorator that only gets run if the function is called with `meander`.

The simplest way to design a handler function is to provide it with a single, unannotated argument. `meander` will pass `Request.content` to this parameter. With this in mind, the `before` functions can alter or augment the `content` attribute using data available in other parts of the `Request` so that the handler function remains unaware of `HTTP`.