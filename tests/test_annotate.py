"""test annotation inspection"""
import pytest

from meander import annotate, types, Request


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
    assert param.type == types.integer  # pylint: disable=comparison-with-callable

    param = params[1]
    assert not param.no_annotation
    assert not param.is_request
    assert not param.is_connection_id
    assert param.is_required
    assert not param.is_extra_kwarg
    assert param.type == str

    param = params[2]
    assert not param.no_annotation
    assert not param.is_request
    assert not param.is_connection_id
    assert not param.is_required
    assert not param.is_extra_kwarg
    assert param.type == types.boolean

    param = params[3]
    assert param.no_annotation
    assert not param.is_request
    assert not param.is_connection_id
    assert param.is_required
    assert param.is_extra_kwarg


# pylint: disable-next=unused-argument
def func4(test1: types.ConnectionId, test2: Request):
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


request = Request()
request.content = {
    "test1": "100",
    "test2": 100,
    "test3": "abc",
    "test4": 1,
    "test5": False,
}
request.args = []


def call_request(abc):
    """expect content"""
    return abc


def call_int(test1: int, test2: int, test4: int):
    """expect ints"""
    return {"a": test1, "b": test2, "c": test4}


def call_str(test1: str, test2: str, test5: str):
    """expect strings"""
    return {"a": test1, "b": test2, "c": test5}


def call_bool(test4: bool, test5: bool):
    """expect booleans"""
    return {"a": test4, "b": test5}


def call_various(test1: int, test2: str, test4: bool, test10: int = 123):
    """expect a combination of things"""
    return {"a": test1, "b": test2, "c": test4, "d": test10}


@pytest.mark.parametrize(
    "func,result",
    (
        (call_request, request.content),
        (call_int, {"a": 100, "b": 100, "c": 1}),
        (call_str, {"a": "100", "b": "100", "c": "False"}),
        (call_bool, {"a": True, "b": False}),
        (call_various, {"a": 100, "b": "100", "c": True, "d": 123}),
    ),
)
def test_call(func, result):
    """test various function signatures"""
    assert annotate.call(func, request) == result
