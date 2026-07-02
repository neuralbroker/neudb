"""FastAPI REST API for neuDB."""

import hmac
import os
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from . import ai_schema


DEFAULT_API_DB_DIR = "neudb_api_data"
IDENTIFIER_PATTERN = r"^[A-Za-z0-9_]+$"
MAX_TEXT_LENGTH = 20_000
MAX_VECTOR_DIMENSIONS = 4096
MAX_TOP_K = 100


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=128, pattern=IDENTIFIER_PATTERN)
    email: str = Field(min_length=1, max_length=320)
    display_name: Optional[str] = Field(default=None, max_length=256)
    metadata: Dict[str, Any] = Field(default_factory=dict, max_length=50)


class SessionCreate(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=512)
    description: str = Field(default="", max_length=MAX_TEXT_LENGTH)
    model: str = Field(default="", max_length=128)
    metadata: Dict[str, Any] = Field(default_factory=dict, max_length=50)


class MessageCreate(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    role: str = Field(min_length=1, max_length=32, pattern=IDENTIFIER_PATTERN)
    content: str = Field(min_length=1, max_length=MAX_TEXT_LENGTH)
    embedding: Optional[List[float]] = Field(default=None, min_length=1, max_length=MAX_VECTOR_DIMENSIONS)
    metadata: Dict[str, Any] = Field(default_factory=dict, max_length=50)


class SearchRequest(BaseModel):
    table: str = Field(default="messages", pattern=IDENTIFIER_PATTERN, max_length=64)
    field: str = Field(default="embedding", pattern=IDENTIFIER_PATTERN, max_length=64)
    text_field: str = Field(default="content", pattern=IDENTIFIER_PATTERN, max_length=64)
    query: Optional[str] = Field(default=None, min_length=1, max_length=MAX_TEXT_LENGTH)
    vector: Optional[List[float]] = Field(default=None, min_length=1, max_length=MAX_VECTOR_DIMENSIONS)
    top_k: int = Field(default=5, ge=1, le=MAX_TOP_K)


def _auth_dependency(expected_api_key: Optional[str]):
    def require_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
        if not expected_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Set NEUDB_API_KEY before enabling the HTTP API.",
            )
        if not x_api_key or not hmac.compare_digest(x_api_key, expected_api_key):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key.")

    return require_api_key


def _record_by_id(db, table_name: str, record_id: str) -> dict:
    records = db.table(table_name).select_by("id", record_id)
    if not records:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return records[0]


def create_app(db_dir: Optional[str] = None, api_key: Optional[str] = None) -> FastAPI:
    """Create a FastAPI app backed by a neuDB directory."""
    db_path = db_dir or os.environ.get("NEUDB_API_DB", DEFAULT_API_DB_DIR)
    expected_api_key = api_key if api_key is not None else os.environ.get("NEUDB_API_KEY")
    require_api_key = _auth_dependency(expected_api_key)
    db = ai_schema.init_ai_database(db_path)
    app = FastAPI(title="neuDB API", version="0.4.1")
    app.state.db = db

    @app.get("/health")
    def health():
        return {"status": "ok", "auth_configured": expected_api_key is not None}

    @app.post("/users", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_api_key)])
    def create_user(payload: UserCreate):
        user_id = ai_schema.add_user(
            db,
            payload.username,
            payload.email,
            display_name=payload.display_name,
            metadata=payload.metadata,
        )
        return {"id": user_id, "user": _record_by_id(db, "users", user_id)}

    @app.post("/sessions", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_api_key)])
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

    @app.post("/messages", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_api_key)])
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

    @app.get("/sessions/{session_id}/messages", dependencies=[Depends(require_api_key)])
    def list_session_messages(session_id: str):
        return {"messages": ai_schema.get_session_messages(db, session_id)}

    @app.post("/search", dependencies=[Depends(require_api_key)])
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
