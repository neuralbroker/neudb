from neudb_ai_schema import *

db = init_ai_database("my_ai_memory")

# Add a user
alice_id = add_user(db, "alice", "alice@example.com", "Alice")
print("Alice user ID:", alice_id)

# Create a session
session_id = create_session(db, alice_id, "Fix Python import error", 
                            "Debugging ModuleNotFoundError", model="codellama-7b")
print("Session ID:", session_id)

# Simulate a conversation
add_message(db, session_id, "user", "I keep getting ModuleNotFoundError: No module named requests")
add_message(db, session_id, "assistant", "Check your Python environment. Try 'pip list'.")

# Tag a message
messages = get_session_messages(db, session_id)
for m in messages:
    if "ModuleNotFoundError" in m["content"]:
        tag_message(db, m["id"], "python")
        tag_message(db, m["id"], "debug")

# Store a memory about the user
add_memory(db, alice_id, "fav_color", "blue", metadata={"source": "chat"})

# Retrieve memory
print("Alice's favorite color:", get_memory(db, alice_id, "fav_color"))

# Show session history
print("\n--- Session History ---")
for m in get_session_messages(db, session_id):
    print(f"[{m['role']}] {m['content']} [tags:{m.get('metadata',{}).get('tags',[])}]")
