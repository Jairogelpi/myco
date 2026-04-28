import json
from unittest.mock import patch, MagicMock
from myco.commons_client import CommonsClient


def test_is_available_false_when_no_url():
    client = CommonsClient("")
    assert client.is_available() is False


def test_is_available_true_when_url_set():
    client = CommonsClient("http://localhost:9000")
    assert client.is_available() is True


def test_search_returns_empty_when_unavailable():
    client = CommonsClient("")
    assert client.search("duckduckgo") == []


def test_publish_returns_none_when_unavailable():
    client = CommonsClient("")
    result = client.publish("skill", "desc", "code", "agent1")
    assert result is None


def test_search_calls_get_with_query():
    client = CommonsClient("http://localhost:9000")
    mock_response = MagicMock()
    mock_response.json.return_value = [{"id": "abc", "name": "skill_ddg"}]
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response) as mock_get:
        result = client.search("duckduckgo")

    mock_get.assert_called_once_with(
        "http://localhost:9000/skills",
        params={"q": "duckduckgo"},
        timeout=10
    )
    assert result == [{"id": "abc", "name": "skill_ddg"}]


def test_search_returns_empty_on_exception():
    client = CommonsClient("http://localhost:9000")
    with patch("httpx.get", side_effect=Exception("timeout")):
        result = client.search("anything")
    assert result == []


def test_publish_posts_correct_payload():
    client = CommonsClient("http://localhost:9000")
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "xyz", "name": "my_skill"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.post", return_value=mock_response) as mock_post:
        result = client.publish("my_skill", "does X", "def run(): pass", "agent42", "research", ["search"])

    mock_post.assert_called_once_with(
        "http://localhost:9000/skills",
        json={
            "name": "my_skill",
            "description": "does X",
            "code": "def run(): pass",
            "agent_id": "agent42",
            "category": "research",
            "tags": ["search"],
        },
        timeout=10,
    )
    assert result == {"id": "xyz", "name": "my_skill"}


def test_get_code_returns_none_on_missing():
    client = CommonsClient("http://localhost:9000")
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("404")
    with patch("httpx.get", return_value=mock_response):
        result = client.get_code("nonexistent")
    assert result is None


def test_record_download_returns_false_when_unavailable():
    client = CommonsClient("")
    assert client.record_download("abc") is False


def test_record_use_returns_false_on_exception():
    client = CommonsClient("http://localhost:9000")
    with patch("httpx.post", side_effect=Exception("network error")):
        assert client.record_use("abc") is False
