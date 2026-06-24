"""LLM agent loop that uses neuDB as long-term memory."""

import argparse
import json
import os
import urllib.error
import urllib.request
from typing import Dict, List, Optional

from . import ai_schema


DEFAULT_SYSTEM_PROMPT = """You are a helpful assistant.
Use the neuDB memory context when it is relevant, but do not mention it unless useful.
If the context is empty or unrelated, answer normally."""


class OllamaClient:
    """Tiny Ollama chat client using Python's standard library."""

    def __init__(self, model: str = "llama3.2", base_url: str = "http://127.0.0.1:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def chat(self, messages: List[Dict[str, str]]) -> str:
        payload = {"model": self.model, "messages": messages, "stream": False}
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Could not reach Ollama at {self.base_url}: {exc}") from exc
        return body.get("message", {}).get("content", "")


class OpenAIClient:
    """Minimal OpenAI chat client using Python's standard library."""

    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("Set OPENAI_API_KEY to use the OpenAI provider.")

    def chat(self, messages: List[Dict[str, str]]) -> str:
        payload = {"model": self.model, "messages": messages}
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Could not reach OpenAI: {exc}") from exc
        return body["choices"][0]["message"]["content"]


class MemoryChatAgent:
    """Chat agent that searches neuDB memories before every response."""

    def __init__(self, db, session_id: str, llm_client, top_k: int = 5, system_prompt: str = DEFAULT_SYSTEM_PROMPT):
        self.db = db
        self.session_id = session_id
        self.llm_client = llm_client
        self.top_k = top_k
        self.system_prompt = system_prompt

    @classmethod
    def create(
        cls,
        db_dir: str = "neudb_agent_memory",
        username: str = "local-user",
        email: str = "local-user@example.com",
        title: str = "Local LLM chat",
        llm_client=None,
        provider: str = "ollama",
        model: Optional[str] = None,
        top_k: int = 5,
    ):
        db = ai_schema.init_ai_database(db_dir)
        user_id = _get_or_create_user(db, username, email)
        session_id = ai_schema.create_session(db, user_id, title, model=model or provider)
        return cls(db, session_id, llm_client or create_llm_client(provider, model), top_k=top_k)

    def retrieve_context(self, user_input: str) -> List[dict]:
        query_vector = ai_schema.embed_text(user_input)
        if query_vector is not None:
            return self.db.table("messages").search_similar("embedding", query_vector, top_k=self.top_k)
        messages = ai_schema.get_session_messages(self.db, self.session_id)
        return messages[-self.top_k:]

    def build_messages(self, user_input: str, context: Optional[List[dict]] = None) -> List[Dict[str, str]]:
        context = self.retrieve_context(user_input) if context is None else context
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": _format_context(context)},
            {"role": "user", "content": user_input},
        ]

    def ask(self, user_input: str) -> str:
        context = self.retrieve_context(user_input)
        messages = self.build_messages(user_input, context=context)
        answer = self.llm_client.chat(messages)
        ai_schema.add_message_with_embedding(
            self.db,
            self.session_id,
            "user",
            user_input,
            metadata={"source": "agent", "context_count": len(context)},
        )
        ai_schema.add_message_with_embedding(
            self.db,
            self.session_id,
            "assistant",
            answer,
            metadata={"source": "agent"},
        )
        return answer


def create_llm_client(provider: str, model: Optional[str] = None):
    if provider == "ollama":
        return OllamaClient(model=model or "llama3.2")
    if provider == "openai":
        return OpenAIClient(model=model or "gpt-4o-mini")
    raise ValueError("provider must be 'ollama' or 'openai'")


def _get_or_create_user(db, username: str, email: str) -> str:
    users = db.table("users")
    existing = users.select_by("username", username)
    if existing:
        return existing[0]["id"]
    return ai_schema.add_user(db, username, email)


def _format_context(messages: List[dict]) -> str:
    if not messages:
        return "Relevant neuDB memory context: none."
    lines = ["Relevant neuDB memory context:"]
    for message in messages:
        role = message.get("role", "unknown")
        content = message.get("content", "")
        lines.append(f"- {role}: {content}")
    return "\n".join(lines)


def run_chat_loop(agent: MemoryChatAgent):
    print("neuDB agent chat. Type 'exit' or 'quit' to stop.")
    while True:
        try:
            user_input = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue
        answer = agent.ask(user_input)
        print(f"assistant> {answer}")


def main():
    parser = argparse.ArgumentParser(description="Run a local LLM chat loop with neuDB memory.")
    parser.add_argument("--provider", choices=["ollama", "openai"], default="ollama")
    parser.add_argument("--model", default=None)
    parser.add_argument("--db", default="neudb_agent_memory")
    parser.add_argument("--username", default="local-user")
    parser.add_argument("--email", default="local-user@example.com")
    parser.add_argument("--title", default="Local LLM chat")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    agent = MemoryChatAgent.create(
        db_dir=args.db,
        username=args.username,
        email=args.email,
        title=args.title,
        provider=args.provider,
        model=args.model,
        top_k=args.top_k,
    )
    run_chat_loop(agent)


if __name__ == "__main__":
    main()
