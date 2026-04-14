"""Tests for the retry utility."""

from unittest.mock import MagicMock, patch, call
import time

import pytest
import requests

from retry import with_retry, retry_request, _calc_delay


class TestCalcDelay:
    def test_exponential_backoff(self):
        assert _calc_delay(0, 1.0, 30.0) == 1.0
        assert _calc_delay(1, 1.0, 30.0) == 2.0
        assert _calc_delay(2, 1.0, 30.0) == 4.0
        assert _calc_delay(3, 1.0, 30.0) == 8.0

    def test_respects_max_delay(self):
        assert _calc_delay(10, 1.0, 5.0) == 5.0

    def test_respects_retry_after_header(self):
        resp = MagicMock()
        resp.headers = {"Retry-After": "3"}
        assert _calc_delay(0, 1.0, 30.0, resp) == 3.0

    def test_retry_after_capped_by_max(self):
        resp = MagicMock()
        resp.headers = {"Retry-After": "60"}
        assert _calc_delay(0, 1.0, 10.0, resp) == 10.0


class TestWithRetryDecorator:
    def test_no_retry_on_success(self):
        call_count = 0

        @with_retry(max_retries=3, base_delay=0)
        def succeeds():
            nonlocal call_count
            call_count += 1
            return "ok"

        assert succeeds() == "ok"
        assert call_count == 1

    def test_retries_on_connection_error(self):
        call_count = 0

        @with_retry(max_retries=2, base_delay=0)
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise requests.ConnectionError("network down")
            return "recovered"

        assert flaky() == "recovered"
        assert call_count == 3

    def test_gives_up_after_max_retries(self):
        @with_retry(max_retries=2, base_delay=0)
        def always_fails():
            raise requests.Timeout("timeout")

        with pytest.raises(requests.Timeout):
            always_fails()

    def test_retries_on_retryable_http_error(self):
        call_count = 0

        @with_retry(max_retries=2, base_delay=0)
        def server_error():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                resp = MagicMock()
                resp.status_code = 503
                raise requests.HTTPError(response=resp)
            return "ok"

        assert server_error() == "ok"
        assert call_count == 2

    def test_does_not_retry_on_4xx(self):
        """Non-retryable HTTP errors (like 400, 401, 403, 404) should not be retried."""
        @with_retry(max_retries=3, base_delay=0)
        def auth_error():
            resp = MagicMock()
            resp.status_code = 401
            raise requests.HTTPError(response=resp)

        with pytest.raises(requests.HTTPError):
            auth_error()


class TestRetryRequest:
    def test_success_on_first_try(self):
        session = MagicMock(spec=requests.Session)
        resp = MagicMock()
        resp.status_code = 200
        session.request.return_value = resp

        result = retry_request("GET", "https://example.com", session=session, max_retries=0)
        assert result == resp

    def test_retries_on_429(self):
        session = MagicMock(spec=requests.Session)

        rate_limited = MagicMock()
        rate_limited.status_code = 429
        rate_limited.headers = {"Retry-After": "0"}

        success = MagicMock()
        success.status_code = 200

        session.request.side_effect = [rate_limited, success]

        result = retry_request("GET", "https://example.com", session=session, base_delay=0)
        assert result == success
        assert session.request.call_count == 2

    def test_retries_on_500(self):
        session = MagicMock(spec=requests.Session)

        error = MagicMock()
        error.status_code = 500
        error.headers = {}

        success = MagicMock()
        success.status_code = 200

        session.request.side_effect = [error, success]

        result = retry_request("GET", "https://api.test.com", session=session, base_delay=0)
        assert result == success

    def test_raises_after_max_retries_on_500(self):
        session = MagicMock(spec=requests.Session)

        error = MagicMock()
        error.status_code = 502
        error.headers = {}
        error.raise_for_status.side_effect = requests.HTTPError(response=error)

        session.request.return_value = error

        with pytest.raises(requests.HTTPError):
            retry_request("GET", "https://api.test.com", session=session, max_retries=2, base_delay=0)

        assert session.request.call_count == 3  # initial + 2 retries
