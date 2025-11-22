import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

from itdepends.integrations import GitHubClient


# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------

def make_response(status_code=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    return resp


# --------------------------------------------------------------------
# Tests do_safe_request
# --------------------------------------------------------------------

def test_do_safe_request_success(monkeypatch):
    client = GitHubClient()

    mock_resp = make_response(200, {"ok": True})
    monkeypatch.setattr(client.session, "get", lambda url: mock_resp)

    data, err = client.do_safe_request("http://example.com")

    assert data == {"ok": True}
    assert err is None


def test_do_safe_request_http_error(monkeypatch):
    client = GitHubClient()

    mock_resp = make_response(404)
    monkeypatch.setattr(client.session, "get", lambda url: mock_resp)

    data, err = client.do_safe_request("http://example.com")

    assert data is None
    assert err == 404


def test_do_safe_request_timeout(monkeypatch):
    client = GitHubClient()

    def raise_timeout(url):
        raise Exception("timeout")

    monkeypatch.setattr(
        client.session,
        "get",
        lambda url: (_ for _ in ()).throw(
            __import__("requests").exceptions.Timeout
        )
    )

    data, err = client.do_safe_request("http://example.com")

    assert data is None
    assert err == "timeout"


# --------------------------------------------------------------------
# Tests verify_repo_existance
# --------------------------------------------------------------------

def test_verify_repo_existance_exists(monkeypatch):
    client = GitHubClient()

    mock_resp = make_response(200)
    monkeypatch.setattr(client.session, "get", lambda url: mock_resp)

    assert client.verify_repo_existance("owner/repo") is True


def test_verify_repo_existance_not_exists(monkeypatch):
    client = GitHubClient()

    mock_resp = make_response(404)
    monkeypatch.setattr(client.session, "get", lambda url: mock_resp)

    assert client.verify_repo_existance("owner/repo") is False


# --------------------------------------------------------------------
# Tests verify_inactivity
# --------------------------------------------------------------------

def test_verify_inactivity_new_repo(monkeypatch):
    client = GitHubClient()

    mock_data = {}
    monkeypatch.setattr(client, "do_safe_request", lambda url: (mock_data, None))

    assert client.verify_inactivity("owner/repo") is True


def test_verify_inactivity_inactive(monkeypatch):
    client = GitHubClient()

    old_date = "2020-01-01T00:00:00Z"
    mock_data = {"pushed_at": old_date}

    monkeypatch.setattr(client, "do_safe_request", lambda url: (mock_data, None))

    # Mock diff_in_months → reporta inatividade
    with patch("itdepends.utils.diff_in_months", return_value=24):
        assert client.verify_inactivity("owner/repo", max_months=6) is True


def test_verify_inactivity_active(monkeypatch):
    client = GitHubClient()

    pushed_at = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    mock_data = {"pushed_at": pushed_at}

    monkeypatch.setattr(client, "do_safe_request", lambda url: (mock_data, None))

    with patch("itdepends.utils.diff_in_months", return_value=2):
        assert client.verify_inactivity("owner/repo", max_months=6) is False


# --------------------------------------------------------------------
# Tests verify_archived
# --------------------------------------------------------------------

def test_verify_archived_true(monkeypatch):
    client = GitHubClient()

    mock_data = {"archived": True}
    monkeypatch.setattr(client, "do_safe_request", lambda url: (mock_data, None))

    assert client.verify_archived("owner/repo") is True


def test_verify_archived_false(monkeypatch):
    client = GitHubClient()

    mock_data = {"archived": False}
    monkeypatch.setattr(client, "do_safe_request", lambda url: (mock_data, None))

    assert client.verify_archived("owner/repo") is False


def test_verify_archived_missing_key(monkeypatch):
    client = GitHubClient()

    mock_data = {}
    monkeypatch.setattr(client, "do_safe_request", lambda url: (mock_data, None))

    assert client.verify_archived("owner/repo") is False