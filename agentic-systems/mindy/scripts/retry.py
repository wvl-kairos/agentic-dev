"""Shared retry utility with exponential backoff."""

import logging
import time
from functools import wraps

import requests

logger = logging.getLogger("mindy.retry")

DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0  # seconds
DEFAULT_MAX_DELAY = 30.0  # seconds

# HTTP status codes worth retrying
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def with_retry(
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    retryable_exceptions: tuple = (requests.ConnectionError, requests.Timeout),
):
    """Decorator that retries a function with exponential backoff.

    Retries on:
    - Network errors (ConnectionError, Timeout)
    - requests.HTTPError with retryable status codes (429, 5xx)
    - Any exception types passed in retryable_exceptions

    For 429 responses, respects the Retry-After header.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except requests.HTTPError as exc:
                    last_exc = exc
                    status = exc.response.status_code if exc.response is not None else 0
                    if status not in RETRYABLE_STATUS_CODES or attempt == max_retries:
                        raise
                    delay = _calc_delay(attempt, base_delay, max_delay, exc.response)
                    logger.warning(
                        "%s: HTTP %d, retrying in %.1fs (attempt %d/%d)",
                        func.__name__, status, delay, attempt + 1, max_retries,
                    )
                    time.sleep(delay)
                except retryable_exceptions as exc:
                    last_exc = exc
                    if attempt == max_retries:
                        raise
                    delay = _calc_delay(attempt, base_delay, max_delay)
                    logger.warning(
                        "%s: %s, retrying in %.1fs (attempt %d/%d)",
                        func.__name__, type(exc).__name__, delay, attempt + 1, max_retries,
                    )
                    time.sleep(delay)
            raise last_exc  # should not reach here, but safety net
        return wrapper
    return decorator


def _calc_delay(attempt: int, base_delay: float, max_delay: float, response=None) -> float:
    """Calculate backoff delay, respecting Retry-After header if present."""
    if response is not None:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return min(float(retry_after), max_delay)
            except ValueError:
                pass
    # Exponential backoff: base * 2^attempt
    return min(base_delay * (2 ** attempt), max_delay)


def retry_request(method: str, url: str, session: requests.Session = None, **kwargs) -> requests.Response:
    """Make an HTTP request with automatic retry on transient failures.

    This is a convenience function for one-off calls without the decorator.
    """
    _session = session or requests.Session()
    max_retries = kwargs.pop("max_retries", DEFAULT_MAX_RETRIES)
    base_delay = kwargs.pop("base_delay", DEFAULT_BASE_DELAY)
    max_delay = kwargs.pop("max_delay", DEFAULT_MAX_DELAY)

    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            resp = _session.request(method, url, **kwargs)
            if resp.status_code in RETRYABLE_STATUS_CODES:
                if attempt == max_retries:
                    resp.raise_for_status()
                delay = _calc_delay(attempt, base_delay, max_delay, resp)
                logger.warning(
                    "HTTP %d from %s, retrying in %.1fs (attempt %d/%d)",
                    resp.status_code, url, delay, attempt + 1, max_retries,
                )
                time.sleep(delay)
                continue
            return resp
        except (requests.ConnectionError, requests.Timeout) as exc:
            last_exc = exc
            if attempt == max_retries:
                raise
            delay = _calc_delay(attempt, base_delay, max_delay)
            logger.warning(
                "%s on %s, retrying in %.1fs (attempt %d/%d)",
                type(exc).__name__, url, delay, attempt + 1, max_retries,
            )
            time.sleep(delay)

    raise last_exc
