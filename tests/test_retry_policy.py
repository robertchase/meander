"""tests for retry_policy"""

import random

import pytest

from meander import retry_policy

RANDOM_SEED = 12321


@pytest.mark.parametrize(
    "kwargs,results",
    (
        ({}, [retry_policy.INITIAL_DELAY_DEFAULT] * 3),
        ({"max_retry": 2}, [retry_policy.INITIAL_DELAY_DEFAULT] * 2),
        ({"max_retry": 2, "jitter_pct": 10}, [1070, 970]),
        ({"max_retry": 1, "initial_delay_ms": 1234, "jitter_pct": 30}, [1295]),
        ({"max_retry": 10, "initial_delay_ms": 567}, [567] * 10),
    ),
)
def test_fixed_backoff(kwargs, results):
    random.seed(RANDOM_SEED)
    backoff = retry_policy.FixedBackoff(**kwargs)
    for result in results:
        assert backoff() == result
    assert backoff() is None


@pytest.mark.parametrize(
    "kwargs,results",
    (
        ({}, [1070, 2040, 3060]),
        ({"max_retry": 2}, [1070, 2040]),
        ({"max_retry": 1, "initial_delay_ms": 4321}, [4623]),
        ({"max_retry": 1, "initial_delay_ms": 4321, "jitter_pct": 20}, [4969]),
        (
            {"max_retry": 10, "initial_delay_ms": 567},
            [606, 1576, 2596, 3566, 4546, 5516, 6536, 7636, 8656, 9606],
        ),
        ({"max_retry": 2, "increase_ms": 100}, [1070, 1167]),
        ({"max_retry": 2, "jitter_pct": 30}, [1050, 2300]),
    ),
)
def test_linear_backoff(kwargs, results):
    random.seed(RANDOM_SEED)
    backoff = retry_policy.LinearBackoff(**kwargs)
    for result in results:
        assert backoff() == result
    assert backoff() is None


@pytest.mark.parametrize(
    "kwargs,results",
    (
        ({}, [1070, 2075, 4233]),
        ({"max_retry": 2}, [1070, 2075]),
        ({"max_retry": 1, "initial_delay_ms": 4321}, [4623]),
        ({"max_retry": 1, "initial_delay_ms": 4321, "jitter_pct": 20}, [4969]),
        (
            {"max_retry": 6, "initial_delay_ms": 567},
            [606, 1175, 2397, 4650, 9114, 17681],
        ),
        ({"max_retry": 2, "multiplier": 3}, [1070, 3113]),
        ({"max_retry": 2, "jitter_pct": 30}, [1050, 2625]),
    ),
)
def test_exponential_backoff(kwargs, results):
    random.seed(RANDOM_SEED)
    backoff = retry_policy.ExponentialBackoff(**kwargs)
    for result in results:
        assert backoff() == result
    assert backoff() is None


def test_retry_basic():
    rp = retry_policy.RetryPolicy()
    assert rp(200) is None
    assert rp(502) == retry_policy.INITIAL_DELAY_DEFAULT
    assert rp(502) == retry_policy.INITIAL_DELAY_DEFAULT
    assert rp(502) == retry_policy.INITIAL_DELAY_DEFAULT
    assert rp(502) is None


def test_retry_linear():
    random.seed(RANDOM_SEED)
    lp = retry_policy.LinearBackoff()
    rp = retry_policy.RetryPolicy(lp, [1, 2, 3])
    assert rp(200) is None
    assert rp(1) == 1070
    assert rp(100) is None
    assert rp(2) == 2040
    assert rp(2) == 3060
    assert rp(2) is None
