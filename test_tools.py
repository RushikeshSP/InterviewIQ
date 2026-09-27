from tools import check_star_structure, detect_filler_words, score_relevance


def test_filler_words_case_insensitive_and_counted():
    result = detect_filler_words("Um, I basically, like, solved it. UM")
    assert result["counts"]["um"] == 2
    assert result["counts"]["like"] == 1
    assert result["counts"]["basically"] == 1
    assert result["total_count"] == 4


def test_star_structure_full_answer():
    result = check_star_structure(
        "During my last project we were behind schedule. I was asked to fix the pipeline. "
        "I debugged the worker and coordinated with the team. As a result, we delivered on time."
    )
    assert result["is_complete"] is True
    assert result["coverage"] == 100


def test_relevance_score():
    result = score_relevance(
        "How do you scale a scraper?",
        "I would use a queue, multiple workers, retry, proxies, rate limiting and monitoring.",
        ["queue", "workers", "retry", "proxy", "rate limit", "monitoring", "storage"],
    )
    assert result["score"] == 86
    assert "storage" in result["missing_concepts"]
