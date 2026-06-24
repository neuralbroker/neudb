# neuDB

A tiny, file-based, AI-native database engine.  
Zero dependencies. Human-readable JSON storage. Semantic search built in.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)

## Features
- **No server, no config** – just a folder of JSON tables.
- **AI‑ready** – store embeddings, search by meaning with cosine similarity.
- **Multi‑user** – sessions, messages, tags, and memory per user.
- **Library + CLI** – `import neudb` or use the command‑line tool.

## Quick start

```bash
# Clone
git clone https://github.com/neuralbroker/neudb.git
cd neudb

# CLI
python neudb.py table create users
python neudb.py row insert users --data '{"username":"alice"}'
python neudb.py row list users

# Library
from neudb import connect
db = connect("mydb")
users = db.table("users")
users.insert({"username": "bob"})
```

## AI memory mode

```python
from neudb.ai_schema import *
db = init_ai_database()
alice = add_user(db, "alice", "alice@example.com")
session = create_session(db, alice, "Chat about Python")
add_message_with_embedding(db, session, "user", "How do I fix an import error?")
```

## Install as a package

```bash
pip install .
# or
pip install -e .
```

Then you can `import neudb` from anywhere.

## HTTP API

Install the API extra and run FastAPI with Uvicorn:

```bash
pip install -e ".[api]"
uvicorn neudb.api:app --reload
```

Open Swagger UI at `http://127.0.0.1:8000/docs`, or use curl:

```bash
curl -X POST http://127.0.0.1:8000/users \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","email":"alice@example.com"}'
```

Set `NEUDB_API_DB=/path/to/db` to choose the API storage directory. By default it uses `neudb_api_data/`.

## License
MIT – see [LICENSE](LICENSE).

## Changelog
See [CHANGELOG.md](CHANGELOG.md).
