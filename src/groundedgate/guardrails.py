"""Deterministic input and output checks; these checks do not prove factual truth."""

import re

from groundedgate.retrieval import Passage
from groundedgate.schemas import Draft, GateCheck

SECRET = re.compile(
    r"sk-ant-[A-Za-z0-9_-]{12,}|"
    r"sk-[A-Za-z0-9_-]{20,}|"
    r"AKIA[0-9A-Z]{16}|"
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"
    r"ANTHROPIC_API_KEY\s*[:=]\s*\S+",
    re.IGNORECASE,
)


def check_question(question: str) -> GateCheck:
    """Block obvious credential strings before retrieval or model calls."""
    safe = bool(question.strip()) and not SECRET.search(question)
    detail = "Question accepted" if safe else "Empty or credential-like input blocked"
    return GateCheck(name="input_secret_scan", passed=safe, detail=detail)


def contains_secret(text: str) -> bool:
    """Detect known credential shapes in a source or generated value."""
    return bool(SECRET.search(text))


def validate_draft(draft: Draft, retrieved: list[Passage]) -> list[GateCheck]:
    """Check output structure and quoted evidence against retrieved passages."""
    by_id = {passage.source_id: passage for passage in retrieved}
    shape = (
        (not draft.claims and len(draft.reason.strip()) >= 10)
        if draft.abstain
        else bool(draft.claims)
    )
    ids_valid = all(claim.source_id in by_id for claim in draft.claims)
    quotes_valid = all(
        claim.source_id in by_id and claim.quote in by_id[claim.source_id].text
        for claim in draft.claims
    )
    distinct = len({(claim.source_id, claim.text) for claim in draft.claims}) == len(draft.claims)
    no_secret = not contains_secret(draft.reason) and all(
        not contains_secret(claim.text) and not contains_secret(claim.quote)
        for claim in draft.claims
    )
    return [
        GateCheck(name="claim_shape", passed=shape, detail="Claims or valid abstention required"),
        GateCheck(name="source_ids", passed=ids_valid, detail="Every source must be retrieved"),
        GateCheck(
            name="exact_quotes", passed=quotes_valid, detail="Quotes must occur in their source"
        ),
        GateCheck(name="unique_claims", passed=distinct, detail="Duplicate claims are rejected"),
        GateCheck(
            name="output_secret_scan", passed=no_secret, detail="No credential pattern detected"
        ),
    ]
