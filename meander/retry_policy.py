"""http retry policy"""
import random


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

        Create a RetryPolicy object, and call the retry method after each
        failure to determine if and how long to wait before retrying the HTTP
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

    def retry(self, http_status_code: int) -> None | int:
        """Return None if no retry should be done, else return int ms delay"""
        if http_status_code not in self.codes:
            return None
        return self.backoff.next()


class FixedBackoff:

    def __init__(self, max_retry=3, initial_delay_ms=100):
        self.max_retry = max_retry
        self.retry = 0
        self.delay = initial_delay_ms

    def calculate(self):
        pass

    def next(self):
        if self.retry == self.max_retry:
            return None
        self.retry += 1
        result = self.delay
        self.calculate()
        return result


class LinearBackoff(FixedBackoff):

    def __init__(self, max_retry=3, initial_delay_ms=100, increase_ms=100):
        super().__init__(max_retry, initial_delay_ms)
        self.increase = increase_ms

    def calculate(self):
        self.delay += self.increase


class ExponentialBackoff:

    def __init__(self, max_retry=3, initial_delay_ms=100, multiplier=2,
                 jitter_pct=10):
        super().__init__(max_retry, initial_delay_ms)
        self.multiplier = multiplier
        self.jitter_pct = jitter_pct

    def calculate(self):
        jitter = random.randint(-self.jitter_pct, self.jitter_pct)
        adjusted_multiplier = self.multiplier * (1 + jitter / 100)
        self.delay = int(self.delay * adjusted_multiplier)
