"""FastAPI REST API for neuDB."""

import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from . import ai_schema


DEFAULT_API_DB_DIR = "neudb_api_data"


class UserCreate(BaseModel):
    username: str
    email: str
    display_name: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SessionCreate(BaseModel):
    user_id: str
    title: str
    description: str = ""
    model: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MessageCreate(BaseModel):
    session_id: str
    role: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchRequest(BaseModel):
    table: str = "messages"
    field: str = "embedding"
    text_field: str = "content"
    query: Optional[str] = None
    vector: Optional[List[float]] = None
    top_k: int = Field(default=5, ge=1)


def _record_by_id(db, table_name: str, record_id: str) -> dict:
    records = db.table(table_name).select_by("id", record_id)
    if not records:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return records[0]


def create_app(db_dir: Optional[str] = None) -> FastAPI:
    """Create a FastAPI app backed by a neuDB directory."""
    db_path = db_dir or os.environ.get("NEUDB_API_DB", DEFAULT_API_DB_DIR)
    db = ai_schema.init_ai_database(db_path)
    app = FastAPI(title="neuDB API", version="0.4.0")
    app.state.db = db

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/users", status_code=status.HTTP_201_CREATED)
    def create_user(payload: UserCreate):
        user_id = ai_schema.add_user(
            db,
            payload.username,
            payload.email,
            display_name=payload.display_name,
            metadata=payload.metadata,
        )
        return {"id": user_id, "user": _record_by_id(db, "users", user_id)}

    @app.post("/sessions", status_code=status.HTTP_201_CREATED)
    def create_session(payload: SessionCreate):
        session_id = ai_schema.create_session(
            db,
            payload.user_id,
            payload.title,
            description=payload.description,
            model=payload.model,
            metadata=payload.metadata,
        )
        return {"id": session_id, "session": _record_by_id(db, "sessions", session_id)}

    @app.post("/messages", status_code=status.HTTP_201_CREATED)
    def create_message(payload: MessageCreate):
        if payload.embedding is None:
            message_id = ai_schema.add_message_with_embedding(
                db,
                payload.session_id,
                payload.role,
                payload.content,
                metadata=payload.metadata,
            )
        else:
            message = {
                "session_id": payload.session_id,
                "role": payload.role,
                "content": payload.content,
                "metadata": payload.metadata,
            }
            message_id = db.table("messages").insert_with_embedding(message, payload.embedding)
        return {"id": message_id, "message": _record_by_id(db, "messages", message_id)}

    @app.get("/sessions/{session_id}/messages")
    def list_session_messages(session_id: str):
        return {"messages": ai_schema.get_session_messages(db, session_id)}

    @app.post("/search")
    def search(payload: SearchRequest):
        if payload.vector is not None:
            query_vector = payload.vector
            results = db.table(payload.table).search_similar(payload.field, query_vector, top_k=payload.top_k)
        elif payload.query:
            query_vector = ai_schema.embed_text(payload.query)
            if query_vector is None:
                results = db.table(payload.table).search_text(payload.text_field, payload.query, top_k=payload.top_k)
            else:
                results = db.table(payload.table).search_similar(payload.field, query_vector, top_k=payload.top_k)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either 'vector' or 'query'.",
            )

        return {"results": results}

    return app


app = create_app()
