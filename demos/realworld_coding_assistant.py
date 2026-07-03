#!/usr/bin/env python3
"""
Real-world use case: local AI coding assistant with persistent memory.

Scenario
--------
You use a local LLM (Ollama, etc.) to debug code. Each chat is a new session,
but you want the assistant to remember:

  - Your stack (Python 3.11, FastAPI, Docker)
  - Fixes that worked last week
  - Past errors similar to today's question

neuDB solves this without Postgres or a vector DB: JSON files on disk,
semantic search over message embeddings, and key-value user memories.

Run:
    python demos/realworld_coding_assistant.py

Requires (optional, for semantic search):
    pip install sentence-transformers
"""

import json
import textwrap
from pathlib import Path

from neudb import cosine_similarity
from neudb.ai_schema import (
    EMBEDDING_AVAILABLE,
    add_memory,
    add_message_with_embedding,
    add_user,
    create_session,
    embed_text,
    get_memory,
    get_session_messages,
    init_ai_database,
    tag_message,
)


DB_DIR = Path(__file__).resolve().parent / "realworld_dev_assistant_data"


def step(number, title, explanation):
    print(f"\n{'=' * 64}")
    print(f"STEP {number}: {title}")
    print(f"{'=' * 64}")
    print(textwrap.fill(explanation, width=64))
    print()


def pause(label, detail=""):
    print(f"→ {label}")
    if detail:
        print(f"  {detail}")


def show_json_files():
    if not DB_DIR.exists():
        return
    print("\n  Files on disk:")
    for path in sorted(DB_DIR.glob("*.json")):
        count = len(json.loads(path.read_text(encoding="utf-8")))
        print(f"    {path.name:<16} {count} records")


def build_agent_context(memories, search_results):
    """Same pattern as neudb.agent.MemoryChatAgent."""
    lines = [
        "Relevant neuDB memory (untrusted quoted data):",
        "--- BEGIN MEMORY ---",
    ]
    for key, value in memories.items():
        lines.append(f"[memory] {key} = {value}")
    for msg in search_results:
        role = msg.get("role", "?")
        content = msg.get("content", "")
        lines.append(f"[{role}] {content}")
    lines.append("--- END MEMORY ---")
    return "\n".join(lines)


def main():
    if DB_DIR.exists():
        import shutil
        shutil.rmtree(DB_DIR)

    # ------------------------------------------------------------------
    step(
        1,
        "Create the database (zero setup)",
        "neuDB is a folder of JSON files — one file per table. "
        "No server, no migrations. You can cat messages.json to debug "
        "what the AI remembered.",
    )
    db = init_ai_database(str(DB_DIR))
    pause("Created tables", "users, sessions, messages, tags, memories")
    show_json_files()

    # ------------------------------------------------------------------
    step(
        2,
        "Register the developer",
        "Multi-user support: each person gets their own sessions, messages, "
        "and memories. In production this maps to auth user IDs.",
    )
    user_id = add_user(
        db,
        "sajad",
        "sajad@dev.local",
        display_name="Sajad",
        metadata={"role": "backend-developer"},
    )
    pause("User created", f"id={user_id[:8]}… username=sajad")

    # ------------------------------------------------------------------
    step(
        3,
        "Store long-term facts (user memories)",
        "Memories are key-value facts about a user — not full chat logs. "
        "Things like preferred Python version or framework. Upsert: same key "
        "updates instead of duplicating.",
    )
    add_memory(db, user_id, "python_version", "3.11")
    add_memory(db, user_id, "stack", "FastAPI + Docker + PostgreSQL")
    add_memory(db, user_id, "venv_path", "~/projects/myapp/.venv")
    pause("Saved 3 memories", "python_version, stack, venv_path")
    pause("Lookup", f"stack = {get_memory(db, user_id, 'stack')}")

    # ------------------------------------------------------------------
    step(
        4,
        "Monday — debugging session (store conversation)",
        "Each chat thread is a session. Every user/assistant turn is a message. "
        "add_message_with_embedding() auto-embeds content so we can search by "
        "meaning later — not just keyword match.",
    )
    monday = create_session(
        db,
        user_id,
        "Fix ModuleNotFoundError",
        description="requests package missing in venv",
        model="llama3.2",
    )
    m1 = add_message_with_embedding(
        db, monday, "user",
        "I keep getting ModuleNotFoundError: No module named requests in my FastAPI app",
    )
    add_message_with_embedding(
        db, monday, "assistant",
        "Activate your venv: source .venv/bin/activate then pip install requests",
    )
    tag_message(db, m1, "python")
    tag_message(db, m1, "debug")
    pause("Session saved", f"2 messages, tags: python, debug")
    show_json_files()

    # ------------------------------------------------------------------
    step(
        5,
        "Wednesday — different problem (another session)",
        "New session = new topic. neuDB keeps all sessions. Search runs "
        "across every stored message, not just the current chat.",
    )
    wednesday = create_session(
        db,
        user_id,
        "Docker deploy fails",
        description="container exits on startup",
        model="llama3.2",
    )
    add_message_with_embedding(
        db, wednesday, "user",
        "My Docker container crashes: ModuleNotFoundError for uvicorn when I run the image",
    )
    add_message_with_embedding(
        db, wednesday, "assistant",
        "Your Dockerfile probably uses system Python. COPY requirements.txt and RUN pip install -r requirements.txt before CMD.",
    )
    pause("Second session saved", "Docker + import error (related to Monday's theme)")

    # ------------------------------------------------------------------
    step(
        6,
        "Thursday — noise session (unrelated chat)",
        "Real apps have off-topic messages. Semantic search should rank "
        "debugging messages higher than small talk for a technical query.",
    )
    thursday = create_session(db, user_id, "Coffee break", model="llama3.2")
    add_message_with_embedding(db, thursday, "user", "What's a good coffee shop nearby?")
    add_message_with_embedding(db, thursday, "assistant", "I don't have location data.")
    pause("Unrelated session saved", "Should rank low for Python errors")

    # ------------------------------------------------------------------
    step(
        7,
        "Friday — developer asks a NEW question (recall phase)",
        "This is what neudb-agent does every turn: embed the new question, "
        "search_similar() on all past messages, pick top_k hits.",
    )
    new_question = "How do I fix import errors when deploying my Python API to production?"
    pause("New question", f'"{new_question}"')

    memories = {
        "python_version": get_memory(db, user_id, "python_version"),
        "stack": get_memory(db, user_id, "stack"),
        "venv_path": get_memory(db, user_id, "venv_path"),
    }

    query_vec = embed_text(new_question)
    messages_table = db.table("messages")

    if query_vec is not None:
        pause("Search mode", "semantic (cosine similarity on embeddings)")
        results = messages_table.search_similar("embedding", query_vec, top_k=4)
    else:
        pause("Search mode", "text fallback (install sentence-transformers for semantic)")
        results = messages_table.search_text("content", "import", top_k=4)

    print("\n  Top matches from past sessions:")
    for i, msg in enumerate(results, 1):
        sim = ""
        if query_vec and msg.get("embedding"):
            sim = f" sim={cosine_similarity(query_vec, msg['embedding']):.3f}"
        preview = msg["content"][:72] + ("…" if len(msg["content"]) > 72 else "")
        print(f"    #{i}{sim} [{msg['role']}] {preview}")

    # ------------------------------------------------------------------
    step(
        8,
        "Inject memory into the LLM prompt",
        "MemoryChatAgent wraps search results in a marked block. The system "
        "prompt treats it as untrusted reference — the model uses it for "
        "context but won't follow instructions hidden inside old messages.",
    )
    context = build_agent_context(memories, results)
    print(context)

    # ------------------------------------------------------------------
    step(
        9,
        "Save today's turn back into neuDB",
        "The loop closes: user question + assistant answer are stored with "
        "embeddings. Next week's similar question will find today's fix too.",
    )
    friday = create_session(
        db, user_id, "Production import error", model="llama3.2",
    )
    add_message_with_embedding(db, friday, "user", new_question)
    simulated_answer = (
        "Based on your past fixes: use your venv locally (~/projects/myapp/.venv) "
        "and in Docker add pip install -r requirements.txt in the Dockerfile."
    )
    add_message_with_embedding(db, friday, "assistant", simulated_answer)
    pause("Friday session saved", "Memory grows automatically each turn")

    # ------------------------------------------------------------------
    step(
        10,
        "Inspect the data (why JSON matters)",
        "Unlike opaque databases, you can read exactly what was stored. "
        "This is critical when debugging AI behavior.",
    )
    print(f"\n  Database path: {DB_DIR}\n")
    show_json_files()
    print("\n  Sample from messages.json (first record):")
    all_msgs = db.table("messages").select_all()
    if all_msgs:
        sample = {k: v for k, v in all_msgs[0].items() if k != "embedding"}
        sample["embedding"] = f"[{len(all_msgs[0].get('embedding') or [])} floats]" if all_msgs[0].get("embedding") else None
        print("  " + json.dumps(sample, indent=2).replace("\n", "\n  "))

    print(f"\n{'=' * 64}")
    print("DONE — this is the same flow as: neudb-agent --provider ollama")
    print(f"Data persisted in: {DB_DIR}")
    if not EMBEDDING_AVAILABLE:
        print("\nTip: pip install sentence-transformers  # enables semantic search")
    print(f"{'=' * 64}\n")


if __name__ == "__main__":
    main()