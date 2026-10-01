"""Run the bounded evidence workflow and fail closed on invalid output."""

from pathlib import Path

from groundedgate.generation import Generator, configured_generator
from groundedgate.guardrails import check_question, contains_secret, validate_draft
from groundedgate.retrieval import Passage, is_instructional_source, load_passages, search
from groundedgate.schemas import AnswerResponse, GateCheck, Source


class AgentService:
    """One retrieval pass, at most one generation call, then deterministic gates."""

    def __init__(self, passages: list[Passage], generator: Generator) -> None:
        self.passages = passages
        self.generator = generator

    @classmethod
    def from_directory(cls, directory: Path) -> "AgentService":
        return cls(load_passages(directory), configured_generator())

    def ask(self, question: str) -> AnswerResponse:
        question = question.strip()
        input_check = check_question(question)
        if not input_check.passed:
            return self._result(
                "blocked", "The request contains a credential-like value.", [input_check]
            )

        eligible = [
            passage
            for passage in self.passages
            if not is_instructional_source(passage.text) and not contains_secret(passage.text)
        ]
        filtered = len(self.passages) - len(eligible)
        source_check = GateCheck(
            name="source_instruction_filter",
            passed=True,
            detail=f"Excluded {filtered} unsafe passage(s)",
        )
        retrieved = search(question, eligible)
        evidence_check = GateCheck(
            name="retrieval_evidence",
            passed=bool(retrieved),
            detail=f"Found {len(retrieved)} passage(s)",
        )
        checks = [input_check, source_check, evidence_check]
        if not retrieved:
            return self._result("abstained", "I could not find relevant evidence.", checks)

        try:
            draft = self.generator.generate(question, retrieved)
        except (RuntimeError, ValueError, KeyError, TypeError, OSError) as exc:
            failed = GateCheck(name="generation", passed=False, detail=type(exc).__name__)
            return self._result("blocked", "Generation failed safely.", checks + [failed])
        except Exception:  # noqa: BLE001 - provider SDK errors vary; fail closed without details
            failed = GateCheck(name="generation", passed=False, detail="Provider error")
            return self._result("blocked", "Generation failed safely.", checks + [failed])

        checks.extend(validate_draft(draft, retrieved))
        if not all(check.passed for check in checks):
            return self._result("blocked", "A validation gate rejected the draft.", checks)
        if draft.abstain:
            return self._result("abstained", draft.reason, checks)

        by_id = {passage.source_id: passage for passage in retrieved}
        answer = "\n".join(f"{claim.text} [{claim.source_id}]" for claim in draft.claims)
        sources = [
            Source(
                source_id=claim.source_id,
                title=by_id[claim.source_id].title,
                quote=claim.quote,
                score=by_id[claim.source_id].score,
            )
            for claim in draft.claims
        ]
        return AnswerResponse(
            status="answered",
            answer=answer,
            sources=sources,
            checks=checks,
            mode=self.generator.mode,
        )

    def _result(self, status: str, answer: str, checks: list[GateCheck]) -> AnswerResponse:
        return AnswerResponse(
            status=status, answer=answer, sources=[], checks=checks, mode=self.generator.mode
        )
