"""Topic query construction and relevance scoring for ArXiv results.

The ArXiv API can return weak matches when a user enters a broad natural-language
phrase. These helpers make ingestion topic-aware by building stricter title /
abstract queries and then reranking/filtering returned papers before persistence.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Sequence

from database import Paper

TOPIC_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "based",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "or",
    "paper",
    "papers",
    "research",
    "study",
    "survey",
    "the",
    "to",
    "using",
    "via",
    "with",
}

SYNONYMS = {
    "llm": ["large", "language", "model"],
    "llms": ["large", "language", "model"],
    "rag": ["retrieval", "augmented", "generation"],
    "nlp": ["natural", "language", "processing"],
    "cv": ["computer", "vision"],
    "rl": ["reinforcement", "learning"],
}


def topic_terms(topic: str) -> list[str]:
    terms = [term for term in re.findall(r"[a-zA-Z][a-zA-Z0-9-]+", topic.lower()) if term not in TOPIC_STOPWORDS]
    expanded: list[str] = []
    for term in terms:
        if term in SYNONYMS:
            expanded.extend(SYNONYMS[term])
            continue
        normalized = term.rstrip("s") if len(term) > 3 else term
        expanded.append(normalized)
    return _dedupe(expanded)


def build_arxiv_query(topic: str) -> str:
    """Build a strict query that favors title/abstract matches for the full topic."""
    terms = topic_terms(topic)
    phrase = " ".join(terms[:6]) or topic.strip()
    escaped_phrase = phrase.replace('"', "")
    if not terms:
        return f'all:"{escaped_phrase}"'
    title_and = " AND ".join(f"ti:{term}" for term in terms[:6])
    abstract_and = " AND ".join(f"abs:{term}" for term in terms[:6])
    all_and = " AND ".join(f"all:{term}" for term in terms[:6])
    return f'(ti:"{escaped_phrase}" OR abs:"{escaped_phrase}" OR ({title_and}) OR ({abstract_and}) OR ({all_and}))'


def rank_topic_relevance(topic: str, papers: Sequence[Paper], limit: int) -> list[Paper]:
    """Return papers ranked by explicit topic overlap, dropping weak matches when possible."""
    if not papers:
        return []
    scored = [(paper, relevance_score(topic, paper)) for paper in papers]
    scored.sort(key=lambda item: (item[1], item[0].published_at), reverse=True)
    strong = [(paper, score) for paper, score in scored if score >= _minimum_score(topic)]
    selected = strong if strong else scored
    return [paper for paper, _ in selected[:limit]]


def relevance_score(topic: str, paper: Paper) -> float:
    terms = topic_terms(topic)
    if not terms:
        return 0.0
    title_tokens = _tokens(paper.title)
    abstract_tokens = _tokens(paper.abstract)
    title_counts = Counter(title_tokens)
    abstract_counts = Counter(abstract_tokens)
    title_hits = sum(1 for term in terms if title_counts[term] or _plural_hit(term, title_counts))
    abstract_hits = sum(1 for term in terms if abstract_counts[term] or _plural_hit(term, abstract_counts))
    phrase = " ".join(terms[:6])
    haystack_title = " ".join(title_tokens)
    haystack_abstract = " ".join(abstract_tokens)
    phrase_bonus = 3.0 if phrase and phrase in haystack_title else 0.0
    phrase_bonus += 1.5 if phrase and phrase in haystack_abstract else 0.0
    coverage = (title_hits + min(abstract_hits, len(terms))) / max(len(terms) * 2, 1)
    return round(title_hits * 2.5 + abstract_hits * 0.8 + phrase_bonus + coverage, 4)


def _minimum_score(topic: str) -> float:
    terms = topic_terms(topic)
    if len(terms) <= 1:
        return 1.0
    return min(4.0, 1.6 + len(terms) * 0.55)


def _tokens(value: str) -> list[str]:
    return [token.rstrip("s") if len(token) > 3 else token for token in re.findall(r"[a-zA-Z][a-zA-Z0-9-]+", value.lower())]


def _plural_hit(term: str, counts: Counter[str]) -> bool:
    return bool(counts[term.rstrip("s")] or counts[f"{term}s"])


def _dedupe(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result
