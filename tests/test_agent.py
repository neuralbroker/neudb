from neudb import ai_schema
from neudb.agent import MemoryChatAgent, _format_context


class FakeLLMClient:
    def __init__(self):
        self.messages = []

    def chat(self, messages):
        self.messages = messages
        return "Remembered answer"


def test_agent_retrieves_context_in_prompt_and_saves_exchange(tmp_path, monkeypatch):
    def fake_embed_text(content):
        if "Python" in content or "import" in content:
            return [1.0, 0.0]
        return [0.0, 1.0]

    monkeypatch.setattr(ai_schema, "embed_text", fake_embed_text)
    db = ai_schema.init_ai_database(str(tmp_path))
    user_id = ai_schema.add_user(db, "alice", "alice@example.com")
    session_id = ai_schema.create_session(db, user_id, "Agent test")
    ai_schema.add_message_with_embedding(db, session_id, "user", "Python import error")
    ai_schema.add_message_with_embedding(db, session_id, "assistant", "Check your virtualenv")

    llm = FakeLLMClient()
    agent = MemoryChatAgent(db, session_id, llm, top_k=1)

    answer = agent.ask("How do I fix this Python import?")

    assert answer == "Remembered answer"
    assert "Python import error" in llm.messages[1]["content"]
    messages = ai_schema.get_session_messages(db, session_id)
    assert messages[-2]["role"] == "user"
    assert messages[-2]["content"] == "How do I fix this Python import?"
    assert messages[-1]["role"] == "assistant"
    assert messages[-1]["content"] == "Remembered answer"


def test_agent_falls_back_to_recent_session_messages_without_embeddings(tmp_path, monkeypatch):
    monkeypatch.setattr(ai_schema, "embed_text", lambda content: None)
    db = ai_schema.init_ai_database(str(tmp_path))
    user_id = ai_schema.add_user(db, "bob", "bob@example.com")
    session_id = ai_schema.create_session(db, user_id, "Fallback test")
    first_id = ai_schema.add_message(db, session_id, "user", "older")
    second_id = ai_schema.add_message(db, session_id, "assistant", "newer")

    agent = MemoryChatAgent(db, session_id, FakeLLMClient(), top_k=1)

    context = agent.retrieve_context("anything")

    assert [message["id"] for message in context] == [second_id]
    assert first_id != second_id


def test_format_context_handles_empty_and_memory_messages():
    assert _format_context([]) == "Relevant neuDB memory context: none."
    assert _format_context([{"role": "user", "content": "hello"}]) == "Relevant neuDB memory context:\n- user: hello"
