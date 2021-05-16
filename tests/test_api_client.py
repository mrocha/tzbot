import api_client as api
import pytest
import requests
import settings

from datetime import datetime
from urllib.parse import urljoin


def test_should_return_datetime_when_successful(tztime, requests_mock):
    requests_mock.get(
        urljoin(settings.TIME_API, "/api/timezone/somewhere"),
        json={"datetime": tztime.isoformat()},
    )
    result = api.get_time_at("somewhere")
    assert tztime == result


def test_should_raise_error_when_timezone_is_invalid(requests_mock):
    requests_mock.get(
        urljoin(settings.TIME_API, "/api/timezone/somewhere"), status_code=404
    )

    with pytest.raises(api.APIError, match="unknown timezone"):
        api.get_time_at("somewhere")

    assert requests_mock.call_count == 1


def test_should_retry_when_http_error(requests_mock):
    requests_mock.get(
        urljoin(settings.TIME_API, "/api/timezone/somewhere"), status_code=500
    )

    with pytest.raises(
        api.APIError, match=r"unable to retrieve time \(http code: 500\)"
    ):
        api.get_time_at("somewhere")

    assert requests_mock.call_count == settings.BACKOFF_MAX_RETRIES


def test_should_retry_when_connection_error(requests_mock):
    requests_mock.get(
        urljoin(settings.TIME_API, "/api/timezone/somewhere"),
        exc=requests.exceptions.ConnectionError,
    )

    with pytest.raises(api.APIError, match="connection error"):
        api.get_time_at("somewhere")

    assert requests_mock.call_count == settings.BACKOFF_MAX_RETRIES


def test_should_retry_when_invalid_json(requests_mock):
    requests_mock.get(urljoin(settings.TIME_API, "/api/timezone/somewhere"), text=".")

    with pytest.raises(api.APIError, match="unknown error"):
        api.get_time_at("somewhere")

    assert requests_mock.call_count == settings.BACKOFF_MAX_RETRIES


@pytest.fixture(autouse=True)
def no_wait_between_retries(monkeypatch):
    monkeypatch.setattr(settings, "BACKOFF_INITIAL_WAIT", 0)
