import pytest
import requests
from unittest.mock import MagicMock, patch
from itdepends.integrations import PyPiClient

# ---------------------------
# Helpers
# ---------------------------

def make_response(status_code=200, json_data=None):
    """Cria um mock de response()."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data or {}
    return mock_resp


# ---------------------------
# Tests do_safe_request
# ---------------------------

def test_do_safe_request_success(monkeypatch):
    client = PyPiClient()

    mock_resp = make_response(
        status_code=200,
        json_data={"ok": True}
    )

    monkeypatch.setattr(client.session, "get", lambda url: mock_resp)

    data, err = client.do_safe_request("http://example.com")

    assert data == {"ok": True}
    assert err is None


def test_do_safe_request_http_error(monkeypatch):
    client = PyPiClient()

    mock_resp = make_response(status_code=404)

    monkeypatch.setattr(client.session, "get", lambda url: mock_resp)

    data, err = client.do_safe_request("http://example.com")

    assert data is None
    assert err == 404


def test_do_safe_request_timeout(monkeypatch):
    client = PyPiClient()

    def raise_timeout(url):
        raise requests.exceptions.Timeout

    monkeypatch.setattr(client.session, "get", raise_timeout)

    data, err = client.do_safe_request("http://example.com")

    assert data is None
    assert err == "timeout"


# ---------------------------
# Tests verify_development_status
# ---------------------------

def test_verify_development_status_ok(monkeypatch):
    client = PyPiClient()

    mock_data = {
        "info": {
            "classifiers": [
                "License :: OSI Approved",
                "Development Status :: 5 - Production/Stable",
            ]
        }
    }

    mock_resp = make_response(200, mock_data)
    monkeypatch.setattr(client, "do_safe_request", lambda url: (mock_data, None))

    ok, status = client.verify_development_status("mypkg")

    assert ok is True
    assert status == "5 - Production/Stable"


def test_verify_development_status_not_found(monkeypatch):
    client = PyPiClient()

    monkeypatch.setattr(client, "do_safe_request", lambda url: (None, 404))

    ok, err = client.verify_development_status("mypkg")

    assert ok is False
    assert err == 404


def test_verify_development_status_no_classifier_match(monkeypatch):
    client = PyPiClient()

    mock_data = {"info": {"classifiers": ["License :: OSI Approved"]}}

    monkeypatch.setattr(client, "do_safe_request", lambda url: (mock_data, None))

    ok, status = client.verify_development_status("mypkg")

    # Expecta sucesso, mas sem Development Status encontrado
    assert ok is True
    assert status is None


# ---------------------------
# Tests get_github_repo_name
# ---------------------------

def test_get_github_repo_ok(monkeypatch):
    client = PyPiClient()

    mock_data = {
        "info": {
            "project_urls": {
                "Homepage": "https://github.com/owner123/repo-name.git",
                "Docs": "https://example.com/docs"
            }
        }
    }

    monkeypatch.setattr(client, "do_safe_request", lambda url: (mock_data, None))

    ok, repo = client.get_github_repo_name("mypkg")

    assert ok is True
    assert repo == "owner123/repo-name"


def test_get_github_repo_no_github(monkeypatch):
    client = PyPiClient()

    mock_data = {
        "info": {
            "project_urls": {
                "Homepage": "https://example.com/home"
            }
        }
    }

    monkeypatch.setattr(client, "do_safe_request", lambda url: (mock_data, None))

    ok, err = client.get_github_repo_name("mypkg")

    assert ok is False
    assert "Couldn't find file" in err


def test_get_github_repo_unparseable_url(monkeypatch):
    client = PyPiClient()

    mock_data = {
        "info": {
            "project_urls": {
                "Homepage": "https://github.com/just-owner-without-repo"
            }
        }
    }

    monkeypatch.setattr(client, "do_safe_request", lambda url: (mock_data, None))

    ok, err = client.get_github_repo_name("mypkg")

    assert ok is False
    assert "couldn't parse owner/repo" in err.lower()


def test_get_github_repo_network_error(monkeypatch):
    client = PyPiClient()

    monkeypatch.setattr(client, "do_safe_request", lambda url: (None, "timeout"))

    ok, err = client.get_github_repo_name("mypkg")

    assert ok is False
    assert err == "timeout"