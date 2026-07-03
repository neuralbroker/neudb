# Changelog

## [Unreleased]

### Added
- Brand assets (`docs/brand/`) — logo, icon, wordmark
- Project documentation index (`docs/README.md`)

## [0.4.1] - 2026-07-02
### Security
- Restricted table and API field identifiers to prevent path traversal.
- Added atomic JSON writes with per-file process locks.
- Added API key protection for HTTP API endpoints.
- Added request size and search limit validation to the HTTP API.
- Hardened LLM memory prompts against prompt injection.
- Restricted Ollama client URLs to localhost by default.

### Added
- `Table.search_text()` full-text fallback for environments without embeddings.

## [0.4.0] – 2026-06-24
### Added
- Built-in semantic search via cosine similarity (pure Python).
- `Table.search_similar()` method and CLI `row search` command.
- `neudb.ai_schema` module with multi-user AI memory helpers.
- Automatic message embedding with `sentence-transformers` (optional).

## [0.3.0] – 2026-06-23
### Added
- Multi-user AI memory schema (users, sessions, messages, tags, memories).
- High-level helper functions: `add_user`, `create_session`, `add_message_with_embedding`, etc.

## [0.2.0] – 2026-06-22
### Added
- Core file-based storage engine (JSON per table).
- CLI interface: `table create`, `row insert/list/find/delete`.
- Library mode: `connect()`, `Table` class.

## [0.1.0] – 2025-06-21
- Conceptual design and schema definition.
