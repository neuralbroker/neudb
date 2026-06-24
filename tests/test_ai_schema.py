from neudb.ai_schema import (
    add_memory,
    add_message,
    add_message_with_embedding,
    add_tag,
    add_user,
    create_session,
    get_memory,
    get_session_messages,
    get_user_sessions,
    get_embedding_model,
    embed_text,
    init_ai_database,
    tag_message,
)


def test_ai_schema_creates_required_tables(tmp_path):
    db = init_ai_database(str(tmp_path))

    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "memories.json",
        "messages.json",
        "sessions.json",
        "tags.json",
        "users.json",
    ]
    assert db.table("users").select_all() == []


def test_ai_schema_user_session_message_and_tag_flow(tmp_path):
    db = init_ai_database(str(tmp_path))

    user_id = add_user(db, "alice", "alice@example.com", "Alice")
    session_id = create_session(db, user_id, "Debugging", model="codellama")
    message_id = add_message(db, session_id, "user", "Import error", metadata={"source": "test"})

    assert get_user_sessions(db, user_id)[0]["id"] == session_id
    assert get_session_messages(db, session_id)[0]["id"] == message_id

    tag_id = add_tag(db, "python")
    assert add_tag(db, "python") == tag_id

    tag_message(db, message_id, "debug")
    tagged_message = db.table("messages").select_by("id", message_id)[0]
    assert tagged_message["metadata"]["tags"] == ["debug"]


def test_ai_schema_memory_upsert_and_lookup(tmp_path):
    db = init_ai_database(str(tmp_path))
    user_id = add_user(db, "bob", "bob@example.com")

    memory_id = add_memory(db, user_id, "favorite_color", "blue")
    updated_memory_id = add_memory(db, user_id, "favorite_color", "green")

    assert updated_memory_id == memory_id
    assert get_memory(db, user_id, "favorite_color") == "green"
    assert get_memory(db, user_id, "missing") is None


def test_add_message_with_embedding_without_optional_dependency(tmp_path, monkeypatch):
    import neudb.ai_schema as ai_schema

    monkeypatch.setattr(ai_schema, "EMBEDDING_AVAILABLE", False)
    monkeypatch.setattr(ai_schema, "EMBED_MODEL", None)

    db = init_ai_database(str(tmp_path))
    user_id = add_user(db, "carol", "carol@example.com")
    session_id = create_session(db, user_id, "No embeddings")

    message_id = add_message_with_embedding(db, session_id, "user", "Hello")
    message = db.table("messages").select_by("id", message_id)[0]

    assert message["embedding"] is None


def test_embedding_model_is_lazy_when_optional_dependency_is_disabled(monkeypatch):
    import neudb.ai_schema as ai_schema

    monkeypatch.setattr(ai_schema, "EMBEDDING_AVAILABLE", False)
    monkeypatch.setattr(ai_schema, "EMBED_MODEL", None)

    assert get_embedding_model() is None
    assert embed_text("hello") is None
