"""call a function with parameter values from a web.Request"""

from dataclasses import dataclass
import inspect

from meander import exception
from meander.document import ServerDocument as Request
from meander import types_


CACHE = {}  # save the results of get_params


def get_params(func):
    """return list of Param instances for each arg/kwarg of 'func'"""

    if func in CACHE:
        return CACHE[func]

    @dataclass
    class Param:
        """container for the attributes of one function parameter"""

        # pylint: disable=too-many-instance-attributes
        type: type
        name: str
        no_annotation: bool
        is_request: bool
        is_connection_id: bool
        is_required: bool
        is_extra_kwarg: bool

    def get_type():
        # pylint: disable=too-many-return-statements
        if par.annotation != par.empty:
            if par.annotation in (Request, types_.ConnectionId):
                return par.annotation
            if par.annotation is int:
                return types_.integer
            if par.annotation is bool:
                return types_.boolean
            if callable(par.annotation):
                return par.annotation
        return lambda x: x

    params = []

    sig = inspect.signature(func)
    for par in sig.parameters.values():
        if par.default == types_.Ignore:
            continue

        param_type = get_type()
        params.append(
            Param(
                param_type,
                par.name,
                par.annotation == par.empty,
                param_type == Request,
                param_type == types_.ConnectionId,
                par.default == par.empty,
                par.kind == par.VAR_KEYWORD,
            )
        )

    CACHE[func] = params

    return params


def call(func, request: Request):
    """call 'func' with args/kwargs from request"""
    # pylint: disable=too-many-branches

    params = get_params(func)

    args = []
    kwargs = {}
    content = request.content
    if len(params) == 0:
        pass
    elif len(params) == 1 and (params[0].no_annotation):
        args.append(content)
    elif len(params) == 1 and (params[0].is_request):
        args.append(request)
    else:
        if not isinstance(content, dict):
            if content is None:
                content = {}
            else:
                raise exception.PayloadValueError(
                    "content", "expecting content to be a dictionary"
                )
        connection_id = f"con={request.connection_id} req={request.id}"

        if len(request.args) > len(params):
            valid = len(params)
            raise exception.ExtraAttributeError(args[valid:])

        for value, param in zip(request.args, params, strict=False):
            if param.name in content:
                raise exception.DuplicateAttributeError(param.name)
            content[param.name] = value

        param_names = [param.name for param in params]
        if extra := [param for param in params if param.is_extra_kwarg]:
            # scoop up extra (unmatched) k/v content into kwargs
            (extra,) = extra
            if extra.name in content:
                raise exception.ExtraAttributeError([extra.name])
            for key in content.keys():
                if key not in param_names:
                    kwargs[key] = content[key]
        else:
            # no ** parameter: check for extra content
            for key in content.keys():
                if key not in param_names:
                    raise exception.ExtraAttributeError([key])

        def update_arguments(param, value):
            if param.is_required:
                args.append(value)
            else:
                kwargs[param.name] = value

        for param in params:
            if param.is_connection_id:
                if param.name in content:
                    raise exception.ExtraAttributeError([param.name])
                update_arguments(param, connection_id)
            elif param.is_request:
                if param.name in content:
                    raise exception.ExtraAttributeError([param.name])
                update_arguments(param, request)
            elif param.is_extra_kwarg:
                pass
            elif param.name not in content:
                if param.is_required:
                    raise exception.RequiredAttributeError(param.name)
            else:
                try:
                    value = param.type(content[param.name])
                    update_arguments(param, value)
                except (AttributeError, ValueError) as err:
                    raise exception.PayloadValueError(param.name, err) from None

    return func(*args, **kwargs)  # will return coroutine if async
