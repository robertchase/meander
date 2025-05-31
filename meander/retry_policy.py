"""http retry policy"""

import random


INITIAL_DELAY_DEFAULT = 1000


class RetryPolicy:
    """HTTP retry policy.

    For use with meander.call.
    """

    def __init__(self, backoff=None, codes: list[int] | None = None):
        """
        backoff - backoff object which determines how long the caller should
                  wait before retry. if not specified, FixedBackoff is used.

        codes - list of HTTP status codes that trigger a retry. if not
                specified, the following codes are used: 408, 429, 502, 503,
                and 504

        Usage:

        Create a RetryPolicy object, and call the policy after each HTTP
        request to determine if and how long to wait before retrying the HTTP
        request. Once the retry method returns a None, retry attempts should
        cease.
        """
        if backoff is None:
            backoff = FixedBackoff()
        self.backoff = backoff
        if codes is None:
            codes = [
                408,  # request timeout
                429,  # too many requests
                502,  # bad gateway
                503,  # service unavailable
                504,  # gateway timeout
            ]
        self.codes = codes

    def __call__(self, http_status_code: int) -> None | int:
        """Return None if no retry should be done, else return int ms delay"""
        if http_status_code not in self.codes:
            return None
        return self.backoff()


def jitter(value, jitter_pct):
    if jitter_pct:
        jitter = random.randint(-jitter_pct, jitter_pct)
        value *= 1 + jitter / 100
    return value


class FixedBackoff:

    def __init__(
        self, max_retry=3, initial_delay_ms=INITIAL_DELAY_DEFAULT, jitter_pct=0
    ):
        self.retry = 0
        self.max_retry = max_retry
        self.initial_delay_ms = initial_delay_ms
        self.jitter_pct = jitter_pct
        self.delay = 0

    def calculate(self):
        return int(jitter(self.initial_delay_ms, self.jitter_pct))

    def __call__(self):
        if self.retry == self.max_retry:
            return None
        self.retry += 1
        if self.retry == 1:
            self.delay = int(jitter(self.initial_delay_ms, self.jitter_pct))
        else:
            self.delay = self.calculate()
        return self.delay


class LinearBackoff(FixedBackoff):

    def __init__(
        self,
        max_retry=3,
        initial_delay_ms=INITIAL_DELAY_DEFAULT,
        increase_ms=INITIAL_DELAY_DEFAULT,
        jitter_pct=10,
    ):
        super().__init__(max_retry, initial_delay_ms, jitter_pct)
        self.increase_ms = increase_ms

    def calculate(self):
        return int(self.delay + jitter(self.increase_ms, self.jitter_pct))


class ExponentialBackoff(FixedBackoff):

    def __init__(
        self,
        max_retry=3,
        initial_delay_ms=INITIAL_DELAY_DEFAULT,
        multiplier=2,
        jitter_pct=10,
    ):
        super().__init__(max_retry, initial_delay_ms, jitter_pct)
        self.multiplier = multiplier

    def calculate(self):
        return int(self.delay * jitter(self.multiplier, self.jitter_pct))
