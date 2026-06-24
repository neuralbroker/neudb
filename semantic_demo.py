from neudb import connect
import math

# Connect to a clean database
db = connect("ai_semantic_demo")

# Create a messages table
messages = db.table("messages")

# Insert some messages with hand‑crafted vectors (2‑dim for demo)
# In reality you'd use a real embedding model like all‑MiniLM‑L6‑v2
messages.insert_with_embedding(
    {"role": "user", "content": "I love Python programming"},
    [0.9, 0.1]   # vector representing "Python/programming"
)
messages.insert_with_embedding(
    {"role": "user", "content": "The weather is sunny today"},
    [0.1, 0.8]   # "weather/sunny"
)
messages.insert_with_embedding(
    {"role": "user", "content": "How do I fix a Python import error?"},
    [0.8, 0.2]   # close to first message
)
messages.insert_with_embedding(
    {"role": "assistant", "content": "Check your Python environment."},
    [0.85, 0.15] # similar to Python topics
)

print("Messages stored.\n")

# Query vector: someone asking about Python errors
query_vec = [0.88, 0.18]

print("Searching for messages similar to 'Python error help'...")
similar = messages.search_similar("embedding", query_vec, top_k=3)

for i, msg in enumerate(similar):
    # Cosine similarity we need to recompute for printing (we didn't return it)
    from neudb import cosine_similarity
    sim = cosine_similarity(query_vec, msg["embedding"])
    print(f"#{i+1} (sim={sim:.3f}) [{msg['role']}] {msg['content']}")
