#!/usr/bin/env python3
"""
neuDB - A tiny, file-based, AI-friendly database with zero dependencies.
Now with built-in semantic search via cosine similarity.

Usage as CLI:
  python neudb.py table create <name>
  python neudb.py row insert <table> --data '<json>'
  python neudb.py row list <table>
  python neudb.py row find <table> --where <key=value>
  python neudb.py row search <table> --field embedding --vector '[0.1,0.2,...]'

Usage as library:
  import neudb
  db = neudb.connect("mydata")
  users = db.table("users")
  users.insert({"username": "alice"})
  users.insert_with_embedding("doc1", {"text":"hello"}, [0.1,0.2])
  results = users.search_similar("embedding", [0.1,0.2])
"""

import json
import os
import sys
import uuid
import math
from typing import Dict, List


# ----------------------------------------------------------------------
# Helper: cosine similarity
# ----------------------------------------------------------------------
def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Return the cosine similarity between two vectors of equal length."""
    if len(vec_a) != len(vec_b):
        raise ValueError("Vectors must be the same length.")
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


# ----------------------------------------------------------------------
# Core engine
# ----------------------------------------------------------------------
class Table:
    """Represents a single table stored as a JSON file."""

    def __init__(self, path: str):
        self.path = path
        self._data: Dict[str, dict] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, 'r') as f:
                self._data = json.load(f)

    def _save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, 'w') as f:
            json.dump(self._data, f, indent=2)

    def insert(self, record: dict) -> str:
        """Insert a record. If no 'id' field, auto-generate UUID."""
        id = record.get("id") or str(uuid.uuid4())
        record["id"] = id
        self._data[id] = record
        self._save()
        return id

    def insert_with_embedding(self, record: dict, embedding: List[float]) -> str:
        """Insert a record and attach an embedding vector."""
        record["embedding"] = embedding
        return self.insert(record)

    def select_all(self) -> List[dict]:
        return list(self._data.values())

    def select_by(self, key: str, value: str) -> List[dict]:
        return [r for r in self._data.values() if str(r.get(key)) == value]

    def update(self, id: str, updates: dict):
        if id in self._data:
            self._data[id].update(updates)
            self._save()

    def delete(self, id: str):
        if id in self._data:
            del self._data[id]
            self._save()

    def exists(self, id: str) -> bool:
        return id in self._data

    def search_similar(self, field: str, query_vector: List[float], top_k: int = 5) -> List[dict]:
        """Return top_k records sorted by cosine similarity of 'field' to query_vector."""
        results = []
        for record in self._data.values():
            vec = record.get(field)
            if vec is not None and isinstance(vec, list):
                try:
                    sim = cosine_similarity(query_vector, vec)
                    results.append((sim, record))
                except ValueError:
                    continue
        # Sort descending by similarity
        results.sort(key=lambda x: x[0], reverse=True)
        return [record for (sim, record) in results[:top_k]]


class Database:
    """A database is a folder containing table files."""

    def __init__(self, db_dir: str):
        self.db_dir = db_dir

    def table(self, name: str) -> Table:
        filename = f"{name}.json"
        path = os.path.join(self.db_dir, filename)
        return Table(path)

    def create_table(self, name: str):
        """Create a new table (just create an empty file)."""
        path = os.path.join(self.db_dir, f"{name}.json")
        if not os.path.exists(path):
            with open(path, 'w') as f:
                json.dump({}, f)
            print(f"Table '{name}' created.")
        else:
            print(f"Table '{name}' already exists.")


def connect(db_dir: str = "neudb_data") -> Database:
    """Connect to (or create) a database directory."""
    os.makedirs(db_dir, exist_ok=True)
    return Database(db_dir)


# ----------------------------------------------------------------------
# CLI interface (extended with search)
# ----------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]
    db = connect()

    if command == "table" and len(sys.argv) >= 4:
        action = sys.argv[2]
        name = sys.argv[3]
        if action == "create":
            db.create_table(name)
        else:
            print("Unknown table action. Use 'create'.")

    elif command == "row":
        if len(sys.argv) < 4:
            print("Usage: row <action> <table> [options]")
            return
        action = sys.argv[2]
        table_name = sys.argv[3]
        table = db.table(table_name)

        if action == "insert":
            if "--data" in sys.argv:
                idx = sys.argv.index("--data")
                data_str = sys.argv[idx + 1]
                record = json.loads(data_str)
                id = table.insert(record)
                print(f"Inserted with ID: {id}")
            else:
                print("Use --data '<json>'")

        elif action == "list":
            rows = table.select_all()
            for row in rows:
                print(row)

        elif action == "find":
            if "--where" in sys.argv:
                idx = sys.argv.index("--where")
                condition = sys.argv[idx + 1]
                if "=" in condition:
                    key, value = condition.split("=", 1)
                    rows = table.select_by(key.strip(), value.strip())
                    for row in rows:
                        print(row)
                else:
                    print("Format: --where key=value")
            else:
                print("Use --where key=value")

        elif action == "delete":
            if "--id" in sys.argv:
                idx = sys.argv.index("--id")
                id = sys.argv[idx + 1]
                table.delete(id)
                print(f"Deleted {id}")
            else:
                print("Use --id <id>")

        elif action == "search":
            if "--field" in sys.argv and "--vector" in sys.argv:
                field_idx = sys.argv.index("--field")
                field_name = sys.argv[field_idx + 1]
                vec_idx = sys.argv.index("--vector")
                vec_str = sys.argv[vec_idx + 1]
                query_vector = json.loads(vec_str)
                results = table.search_similar(field_name, query_vector)
                for row in results:
                    print(row)
            else:
                print("Usage: row search <table> --field <field_name> --vector '[0.1,0.2,...]'")

        else:
            print("Unknown row action. Use: insert, list, find, delete, search.")

    else:
        print("Unknown command. Use 'table' or 'row'.")


if __name__ == "__main__":
    main()
