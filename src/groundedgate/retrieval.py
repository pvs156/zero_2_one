"""Deterministic local Markdown loading, chunking, and BM25 retrieval."""

import re
from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from math import log
from pathlib import Path

TOKEN = re.compile(r"[a-z0-9]{2,}", re.IGNORECASE)
STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "can",
        "do",
        "does",
        "for",
        "from",
        "how",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "the",
        "to",
        "was",
        "were",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "with",
    }
)
INSTRUCTION = re.compile(
    r"ignore (all |any |the )?(previous|prior|above) instructions|"
    r"reveal (the |your )?(system prompt|api key|secret)|"
    r"send (the |your )?(api key|secret) to|"
    r"you are now (the |a )?system",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Passage:
    source_id: str
    title: str
    text: str
    score: float = 0.0


def tokenize(value: str) -> list[str]:
    return [
        match.group().lower()
        for match in TOKEN.finditer(value)
        if match.group().lower() not in STOPWORDS
    ]


def _chunks(text: str, limit: int = 900) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    chunks: list[str] = []
    for paragraph in paragraphs:
        for start in range(0, len(paragraph), limit):
            chunk = paragraph[start : start + limit].strip()
            if chunk:
                chunks.append(chunk)
    return chunks


def load_passages(directory: Path) -> list[Passage]:
    """Load bounded UTF-8 Markdown files from one local directory.

    Args:
        directory: Existing directory containing the trusted demo corpus.

    Returns:
        Stable passages with content-derived IDs.

    Raises:
        ValueError: If the directory or a document violates the corpus limits.
    """
    if not directory.is_dir():
        raise ValueError(f"Document directory does not exist: {directory}")
    files = sorted(directory.glob("*.md"))
    if len(files) > 100:
        raise ValueError("Document limit exceeded (100)")
    passages: list[Passage] = []
    for path in files:
        if path.is_symlink() or not path.is_file():
            continue
        if path.stat().st_size > 100_000:
            raise ValueError(f"Document exceeds 100 KB: {path.name}")
        body = path.read_text(encoding="utf-8")
        title = next(
            (line[2:].strip() for line in body.splitlines() if line.startswith("# ")), path.stem
        )
        for index, chunk in enumerate(_chunks(body)):
            source_id = sha256(f"{path.name}:{index}:{chunk}".encode()).hexdigest()[:10]
            passages.append(Passage(source_id=source_id, title=title, text=chunk))
            if len(passages) > 1000:
                raise ValueError("Passage limit exceeded (1000)")
    return passages


def is_instructional_source(text: str) -> bool:
    """Flag common instructions embedded in source content.

    This is a narrow heuristic, not a comprehensive prompt-injection detector.
    """
    return bool(INSTRUCTION.search(text))


def search(question: str, passages: list[Passage], limit: int = 4) -> list[Passage]:
    """Return up to `limit` relevant passages using local BM25 scoring."""
    corpus = [passage for passage in passages if not is_instructional_source(passage.text)]
    if not corpus:
        return []
    tokens = [tokenize(passage.text) for passage in corpus]
    frequencies = [Counter(words) for words in tokens]
    document_frequencies = Counter(term for counts in frequencies for term in counts)
    average_length = sum(len(words) for words in tokens) / len(tokens)
    terms = set(tokenize(question))
    if not terms or average_length == 0:
        return []
    ranked: list[Passage] = []
    for passage, words, counts in zip(corpus, tokens, frequencies, strict=True):
        score = 0.0
        for term in terms:
            frequency = counts[term]
            if frequency == 0:
                continue
            document_frequency = document_frequencies[term]
            inverse_frequency = log(
                1 + (len(corpus) - document_frequency + 0.5) / (document_frequency + 0.5)
            )
            denominator = frequency + 1.2 * (0.25 + 0.75 * len(words) / average_length)
            score += inverse_frequency * frequency * 2.2 / denominator
        if score > 0:
            ranked.append(Passage(passage.source_id, passage.title, passage.text, round(score, 6)))
    return sorted(ranked, key=lambda item: (-item.score, item.title, item.source_id))[:limit]
