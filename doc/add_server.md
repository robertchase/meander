# add_server

Add a listening port along with handlers for each resource that the port provides. The port will begin accepting connections after `web.run` is called.

```
add_server(
    routes: dict,
    name: str = None,
    port: int = 8080,
    base_url: str = None,
    ssl_certfile: str = None,
    ssl_keyfile: str = None
)
```

### routes

The `routes` parameter defines a set of `HTTP` resources and associated handlers. Each `HTTP` document sent to the server will be matched against the items in `routes`. The handler associated with the first match will be executed; if no match is found, `meander` will respond with a `404`.

`routes` is a dict of the form:

```
{
    "pattern": HANDLER,
    "pattern": {
        "method": HANDLER,
        "method": {control-parameters},...
    },...
}
```

where:

* `pattern` is a regex matching an http_resorce (path); the pattern must match the complete resource
* `method` is a string matching an http_method (`GET`, `POST`, etc)
* `HANDLER` is an http handler (callable), or a dot-delimited path to an http handler (dynamically loaded), or a simple string (returned on match)
* `control-parameters` is a dict containing:

		"handler": HANDLER
	
	and any of:
	
		"silent": True|False
		"before": [callable, ...]

* `silent` is a flag that controls log messages produced by meander for each connection (default=False)
* `before` is a list of callables to execute prior to calling the
handler; each callable is invoked in order with a `meander.Request` as the only argument
	
If a pattern has only a `GET` method handler, then the dict of methods and handlers can be replaced with just a `HANDLER`.

### name
`name` is assigned to the server. This is used in log messages and is helpful in differentiating multiple servers.

### port

`port` is the TCP listening port for the server. Multiple calls to `add_server` must use different values for `port`.

### base_url

If every http_resource starts with the same characters, then these characters can be specified with `base_url`. If `base_url` is specified, then the `pattern` in each `route` will be prepended with the `base_url` value before being matched.

### ssl\_certfile and ssl_keyfile

These parameters must either be specified together, or absent. If present, they will configure the server to start as HTTPS. 