from neudb import connect, cosine_similarity
from neudb_ai_schema import *

db = init_ai_database("ai_real_memory")

alice = add_user(db, "alice", "alice@example.com", "Alice")
session = create_session(db, alice, "Debugging Python import error", model="codellama")

add_message_with_embedding(db, session, "user", "I keep getting ModuleNotFoundError: No module named requests")
add_message_with_embedding(db, session, "assistant", "Check which Python environment you are using.")
add_message_with_embedding(db, session, "user", "How do I install packages inside a virtual environment?")
add_message_with_embedding(db, session, "assistant", "Activate the venv and then run pip install.")
add_message_with_embedding(db, session, "user", "The weather is really nice today!")

query_text = "help with Python import errors"
if EMBEDDING_AVAILABLE:
    query_vec = EMBED_MODEL.encode(query_text).tolist()
    print(f"Searching for: '{query_text}'\n")
    messages_table = db.table("messages")
    results = messages_table.search_similar("embedding", query_vec, top_k=3)
    for i, msg in enumerate(results):
        sim = cosine_similarity(query_vec, msg["embedding"])
        print(f"#{i+1} (sim={sim:.3f}) [{msg['role']}] {msg['content']}")
else:
    print("Please install sentence-transformers: pip install sentence-transformers")
