"""Credential-free regression evaluation for the sample corpus."""

import json
from pathlib import Path

from groundedgate.generation import OfflineGenerator
from groundedgate.retrieval import load_passages
from groundedgate.service import AgentService

ROOT = Path(__file__).resolve().parents[2]


def evaluate() -> dict[str, object]:
    """Score expected status, source selection, and citation checks."""
    cases = json.loads((ROOT / "data" / "evals.json").read_text(encoding="utf-8"))
    service = AgentService(load_passages(ROOT / "data" / "knowledge"), OfflineGenerator())
    results = []
    for case in cases:
        response = service.ask(case["question"])
        expected_source = case["source"]
        source_ok = expected_source is None or any(
            source.title == expected_source for source in response.sources
        )
        gates_ok = all(
            check.passed for check in response.checks if check.name != "retrieval_evidence"
        )
        passed = response.status == case["status"] and source_ok and gates_ok
        results.append({"question": case["question"], "passed": passed, "status": response.status})
    return {
        "mode": "offline",
        "cases": len(results),
        "passed": sum(result["passed"] for result in results),
        "pass_rate": round(sum(result["passed"] for result in results) / len(results), 3),
        "results": results,
    }


def main() -> None:
    """Print machine-readable results and fail when a sample case regresses."""
    report = evaluate()
    print(json.dumps(report, indent=2))
    if report["passed"] != report["cases"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
