from dataclasses import dataclass
from inspect import signature

from meander import exception, Request
from meander.param import types


CACHE = {}


def get_params(fn):

    if fn in CACHE:
        return CACHE[fn]

    @dataclass
    class Param:
        type: type
        name: str
        no_annotation: bool
        is_request: bool
        is_connection_id: bool
        is_skip: bool
        is_required: bool
        is_extra_kwarg: bool

    def get_type():
        if par.annotation != par.empty:
            if par.annotation in (Request, types.ConnectionId, types.SkipParam):
                return par.annotation
            if par.annotation == int:
                return types.integer
            if par.annotation == bool:
                return types.boolean
            if par.annotation == str:
                return str
            if isinstance(par.annotation, type) and \
                    issubclass(par.annotation, types.ParamType):
                return par.annotation()
            if isinstance(par.annotation, types.ParamType):
                return par.annotation
        return lambda x: x

    params = []

    sig = signature(fn)
    for par in sig.parameters.values():

        param_type = get_type()

        param = Param(
            param_type,
            par.name,
            par.annotation == par.empty,
            param_type == Request,
            param_type == types.ConnectionId,
            param_type == types.SkipParam,
            par.default == par.empty,
            par.kind == par.VAR_KEYWORD,
        )

        if not param.is_skip:
            params.append(param)

    CACHE[fn] = params

    return params


def call(fn, request: Request):

    params = get_params(fn)

    args = []
    kwargs = {}
    if len(params) == 0:
        pass
    elif len(params) == 1 and (params[0].no_annotation or params[0].is_request):
        args.append(request)
    else:
        content = request.content
        if not isinstance(content, dict):
            raise exception.PayloadValueError(
                "expecting content to be a dictionary")
        connection_id = f"con={request.connection_id} req={request.id}"

        if len(request.args) > len(params):
            raise exception.ExtraAttributeError(args[len(params):])

        for value, param in zip(request.args, params):
            if param.name in content:
                raise exception.DuplicateAttributeError(param.name)
            content[param.name] = value

        if True in [param.is_extra_kwarg for param in params]:
            param_names = [param.name for param in params]
            for key, val in content:
                if key not in param_names:
                    kwargs[key] = val

        def update_arguments(param, value):
            if param.is_required:
                args.append(value)
            else:
                kwargs[param.name] = value

        for param in params:
            if param.is_connection_id:
                update_arguments(param, connection_id)
            elif param.is_request:
                update_arguments(param, request)
            elif param.name not in content:
                if param.is_required:
                    raise exception.RequiredAttributeError(param.name)
            else:
                try:
                    value = param.type(content[param.name])
                    update_arguments(param, value)
                except ValueError as err:
                    raise exception.PayloadValueError(f"'{param.name}' is {err}")

    return fn(*args, **kwargs)
