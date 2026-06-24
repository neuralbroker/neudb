from fastapi.testclient import TestClient

import neudb.ai_schema as ai_schema
from neudb.api import create_app


def test_api_user_session_message_flow(tmp_path, monkeypatch):
    monkeypatch.setattr(ai_schema, "EMBEDDING_AVAILABLE", False)
    monkeypatch.setattr(ai_schema, "EMBED_MODEL", None)
    client = TestClient(create_app(str(tmp_path)))

    user_response = client.post(
        "/users",
        json={"username": "alice", "email": "alice@example.com", "display_name": "Alice"},
    )
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]

    session_response = client.post(
        "/sessions",
        json={"user_id": user_id, "title": "Debugging", "model": "codellama"},
    )
    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    message_response = client.post(
        "/messages",
        json={"session_id": session_id, "role": "user", "content": "How do I fix imports?"},
    )
    assert message_response.status_code == 201
    assert message_response.json()["message"]["embedding"] is None

    messages_response = client.get(f"/sessions/{session_id}/messages")
    assert messages_response.status_code == 200
    messages = messages_response.json()["messages"]
    assert len(messages) == 1
    assert messages[0]["content"] == "How do I fix imports?"


def test_api_search_with_vector(tmp_path, monkeypatch):
    monkeypatch.setattr(ai_schema, "EMBEDDING_AVAILABLE", False)
    monkeypatch.setattr(ai_schema, "EMBED_MODEL", None)
    client = TestClient(create_app(str(tmp_path)))

    first = client.post(
        "/messages",
        json={"session_id": "s1", "role": "user", "content": "Python", "embedding": [1.0, 0.0]},
    )
    second = client.post(
        "/messages",
        json={"session_id": "s1", "role": "user", "content": "Weather", "embedding": [0.0, 1.0]},
    )

    response = client.post("/search", json={"vector": [1.0, 0.0], "top_k": 1})

    assert response.status_code == 200
    assert response.json()["results"] == [first.json()["message"]]
    assert second.json()["message"] not in response.json()["results"]


def test_api_search_requires_query_or_vector(tmp_path):
    client = TestClient(create_app(str(tmp_path)))

    response = client.post("/search", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "Provide either 'vector' or 'query'."
