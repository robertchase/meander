"""test annotation inspection"""

import pytest

from meander import annotate, types_, Request, exception


def func1():
    """empty parameter list"""


def test_get_params_empty():
    """verify get_params result with no params"""
    params = annotate.get_params(func1)
    assert params == []


def func2(test):  # pylint: disable=unused-argument
    """single un-annotated parameter"""


def test_get_params_single():
    """verify get_params result with one unannotated param"""
    params = annotate.get_params(func2)
    assert len(params) == 1
    param = params[0]
    assert param.no_annotation
    assert not param.is_request
    assert not param.is_connection_id
    assert param.is_required
    assert not param.is_extra_kwarg


# pylint: disable-next=unused-argument
def func3(test1: int, test2: str, test3: bool = True, **kwargs):
    """multiple parameters"""


def test_get_params_multiple():
    """verify get_params result with several arguments"""
    params = annotate.get_params(func3)
    assert len(params) == 4

    param = params[0]
    assert not param.no_annotation
    assert not param.is_request
    assert not param.is_connection_id
    assert param.is_required
    assert not param.is_extra_kwarg
    assert param.type == types_.integer

    param = params[1]
    assert not param.no_annotation
    assert not param.is_request
    assert not param.is_connection_id
    assert param.is_required
    assert not param.is_extra_kwarg
    assert param.type is str

    param = params[2]
    assert not param.no_annotation
    assert not param.is_request
    assert not param.is_connection_id
    assert not param.is_required
    assert not param.is_extra_kwarg
    assert param.type == types_.boolean

    param = params[3]
    assert param.no_annotation
    assert not param.is_request
    assert not param.is_connection_id
    assert param.is_required
    assert param.is_extra_kwarg


# pylint: disable-next=unused-argument
def func4(test1: types_.ConnectionId, test2: Request):
    """special parameters"""


def test_get_params_special():
    """verify get_params result with special arguments"""
    params = annotate.get_params(func4)
    assert len(params) == 2

    param = params[0]
    assert not param.no_annotation
    assert not param.is_request
    assert param.is_connection_id
    assert param.is_required
    assert not param.is_extra_kwarg

    param = params[1]
    assert not param.no_annotation
    assert param.is_request
    assert not param.is_connection_id
    assert param.is_required
    assert not param.is_extra_kwarg


def test_special_values():
    """ConnectionId and Request can't be specified in content, since they are
    automatically assigned by annotate.call.
    """
    request = Request()
    request.args = []

    request.content = {"test1": 1}  # can't specify ConnectionId
    with pytest.raises(exception.ExtraAttributeError):
        annotate.call(func4, request)

    request.content = {"test2": 1}  # can't specify Request
    with pytest.raises(exception.ExtraAttributeError):
        annotate.call(func4, request)


request = Request()
request.content = {
    "test1": "100",
    "test2": 100,
    "test3": "abc",
    "test4": 1,
    "test5": False,
}
request.args = []


def call_request(abc: Request):
    """expect request"""
    return abc


def call_content(abc):
    """expect content"""
    return abc


# pylint: disable-next=unused-argument
def call_int(test1: int, test2: int, test4: int, **kwargs):
    """expect ints"""
    return {"a": test1, "b": test2, "c": test4}


# pylint: disable-next=unused-argument
def call_str(test1: str, test2: str, test5: str, **kwargs):
    """expect strings"""
    return {"a": test1, "b": test2, "c": test5}


# pylint: disable-next=unused-argument
def call_bool(test4: bool, test5: bool, **kwargs):
    """expect booleans"""
    return {"a": test4, "b": test5}


# pylint: disable-next=unused-argument
def call_various(test1: int, test2: str, test4: bool, test10: int = 123, **kwargs):
    """expect a combination of things"""
    return {"a": test1, "b": test2, "c": test4, "d": test10}


@pytest.mark.parametrize(
    "func,result",
    (
        (call_request, request),
        (call_content, request.content),
        (call_int, {"a": 100, "b": 100, "c": 1}),
        (call_str, {"a": "100", "b": "100", "c": "False"}),
        (call_bool, {"a": True, "b": False}),
        (call_various, {"a": 100, "b": "100", "c": True, "d": 123}),
    ),
)
def test_call(func, result):
    """test various function signatures"""
    assert annotate.call(func, request) == result


def test_non_json_call():
    """check for non-json content when annotated arguments are specified"""
    non_json_request = Request()
    non_json_request.content = ""
    non_json_request.args = []
    with pytest.raises(exception.PayloadValueError):
        annotate.call(call_int, non_json_request)


def call_one(test1: int):  # pylint: disable=unused-argument
    """Single argument."""


def test_extra_parameter():
    """Send undefined parameter and expect error."""
    request.content = {"test1": 1, "test2": 2}
    with pytest.raises(exception.ExtraAttributeError):
        annotate.call(call_one, request)


def call_with_kwargs(test: int, **test_kwargs):  # pylint: disable=unused-argument
    """Test ** argument."""
    return test_kwargs


def test_extra_parameter_with_kwargs():
    """Send undefined parameter and expect success."""
    request.content = {"test": 1, "a": 10, "b": 12}
    result = annotate.call(call_with_kwargs, request)
    assert result == {"a": 10, "b": 12}


def test_conflict_with_kwargs():
    """Send parameter name that conflicts with **kwarg name."""
    request.content = {"test": 1, "test_kwargs": 10}
    with pytest.raises(exception.ExtraAttributeError):
        annotate.call(call_with_kwargs, request)
