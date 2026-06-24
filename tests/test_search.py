from neudb import cosine_similarity, connect


def test_cosine_similarity_with_matching_and_zero_vectors():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0


def test_cosine_similarity_rejects_different_lengths():
    try:
        cosine_similarity([1.0], [1.0, 0.0])
    except ValueError as exc:
        assert str(exc) == "Vectors must be the same length."
    else:
        raise AssertionError("cosine_similarity should reject vectors with different lengths")


def test_search_similar_returns_top_matches_in_order(tmp_path):
    db = connect(str(tmp_path))
    messages = db.table("messages")
    python_id = messages.insert_with_embedding({"content": "Python help"}, [1.0, 0.0])
    docs_id = messages.insert_with_embedding({"content": "Python docs"}, [0.8, 0.2])
    messages.insert_with_embedding({"content": "Weather"}, [0.0, 1.0])
    messages.insert({"content": "No embedding"})

    results = messages.search_similar("embedding", [1.0, 0.0], top_k=2)

    assert [record["id"] for record in results] == [python_id, docs_id]


def test_search_similar_skips_mismatched_vector_dimensions(tmp_path):
    db = connect(str(tmp_path))
    messages = db.table("messages")
    valid_id = messages.insert_with_embedding({"content": "Valid"}, [1.0, 0.0])
    messages.insert_with_embedding({"content": "Wrong dimension"}, [1.0, 0.0, 0.0])

    results = messages.search_similar("embedding", [1.0, 0.0], top_k=5)

    assert [record["id"] for record in results] == [valid_id]


def test_search_text_matches_case_insensitive_substrings(tmp_path):
    db = connect(str(tmp_path))
    messages = db.table("messages")
    first_id = messages.insert({"content": "Python import help"})
    second_id = messages.insert({"content": "More PYTHON notes"})
    messages.insert({"content": "Weather report"})

    results = messages.search_text("content", "python", top_k=5)

    assert [record["id"] for record in results] == [first_id, second_id]


def test_search_text_honors_top_k_and_empty_query(tmp_path):
    db = connect(str(tmp_path))
    messages = db.table("messages")
    first_id = messages.insert({"content": "Python one"})
    messages.insert({"content": "Python two"})

    assert [record["id"] for record in messages.search_text("content", "python", top_k=1)] == [first_id]
    assert messages.search_text("content", "") == []
