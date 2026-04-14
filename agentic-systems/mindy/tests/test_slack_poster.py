from unittest.mock import MagicMock, patch, call

import pytest
import requests

import slack_poster


def _mock_session():
    """Create a mock session that returns Slack success responses."""
    session = MagicMock(spec=requests.Session)
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"ok": True, "ts": "123.456"}
    response.raise_for_status = MagicMock()
    session.post.return_value = response
    return session


class TestPostMessage:
    def test_returns_ts_on_success(self):
        session = _mock_session()
        ts = slack_poster.post_message("C123", "hello", session)
        assert ts == "123.456"

    def test_raises_on_slack_api_error(self):
        session = _mock_session()
        session.post.return_value.json.return_value = {"ok": False, "error": "channel_not_found"}
        with pytest.raises(RuntimeError, match="channel_not_found"):
            slack_poster.post_message("C123", "hello", session)

    def test_passes_correct_payload(self):
        session = _mock_session()
        slack_poster.post_message("C123", "hello", session)
        session.post.assert_called_once()
        payload = session.post.call_args[1]["json"]
        assert payload["channel"] == "C123"
        assert payload["text"] == "hello"


class TestPostThreadReply:
    def test_passes_thread_ts(self):
        session = _mock_session()
        slack_poster.post_thread_reply("C123", "ts-parent", "reply", session)
        payload = session.post.call_args[1]["json"]
        assert payload["thread_ts"] == "ts-parent"


class TestSplitAndPost:
    def test_short_message_no_split(self):
        with patch("slack_poster._make_session") as mock_sess:
            mock_sess.return_value = _mock_session()
            with patch("slack_poster.post_message", return_value="ts-001") as mock_post:
                ts = slack_poster.split_and_post("C123", "hello", "token")
        assert ts == "ts-001"

    def test_exactly_at_limit_no_split(self):
        text = "x" * slack_poster.SLACK_MAX_CHARS
        with patch("slack_poster._make_session") as mock_sess:
            mock_sess.return_value = _mock_session()
            with patch("slack_poster.post_message", return_value="ts-002") as mock_post:
                slack_poster.split_and_post("C123", text, "token")
        mock_post.assert_called_once()

    def test_long_message_splits_on_newline(self):
        part1 = "A" * 1800 + "\n"
        part2 = "B" * 200
        text = part1 + part2
        with patch("slack_poster._make_session") as mock_sess:
            mock_sess.return_value = _mock_session()
            with patch("slack_poster.post_message", return_value="ts-003") as m_post, \
                 patch("slack_poster.post_thread_reply") as m_reply:
                slack_poster.split_and_post("C123", text, "token")
        assert m_post.call_count == 1
        assert m_reply.call_count == 1

    def test_no_newline_forces_hard_cut(self):
        text = "X" * 2500  # no newlines
        with patch("slack_poster._make_session") as mock_sess:
            mock_sess.return_value = _mock_session()
            with patch("slack_poster.post_message", return_value="ts-004") as m_post, \
                 patch("slack_poster.post_thread_reply") as m_reply:
                slack_poster.split_and_post("C123", text, "token")
        posted_main = m_post.call_args[0][1]
        assert len(posted_main) == slack_poster.SLACK_MAX_CHARS

    def test_empty_string(self):
        with patch("slack_poster._make_session") as mock_sess:
            mock_sess.return_value = _mock_session()
            with patch("slack_poster.post_message", return_value="ts-empty") as mock_post:
                ts = slack_poster.split_and_post("C123", "", "token")
        mock_post.assert_called_once()
        assert ts == "ts-empty"


class TestRetryLogic:
    def test_retries_on_429(self):
        session = MagicMock(spec=requests.Session)
        rate_limited = MagicMock()
        rate_limited.status_code = 429
        rate_limited.headers = {"Retry-After": "0"}

        success = MagicMock()
        success.status_code = 200
        success.json.return_value = {"ok": True, "ts": "999"}
        success.raise_for_status = MagicMock()

        session.post.side_effect = [rate_limited, success]

        data = slack_poster._post_with_retry({"channel": "C1", "text": "hi"}, session)
        assert data["ts"] == "999"
        assert session.post.call_count == 2
