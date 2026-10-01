# GroundedGate quality model

GroundedGate treats model output as a proposal, not a final answer. The release decision is made by deterministic code. Every result includes a validation receipt so failures are visible.

## Boundaries

- **User input:** The API accepts one bounded question. Obvious credential patterns are rejected. This is pattern screening, not full secret detection.
- **Source material:** The demo reads local UTF-8 Markdown only. File and corpus limits bound work. Symlinks are skipped. Source text is treated as data; passages with common instruction or credential patterns are excluded.
- **Retrieval:** BM25 produces a repeatable top four list. No positive match means abstention. A lexical match is not proof of relevance.
- **Generation:** The optional model receives only the question and retrieved passages and has one bounded call. The offline generator copies an evidence sentence verbatim and is labeled as a demo.
- **Release:** A strict claim object needs a retrieved ID and an exact quote. The answer is constructed from validated claims. Invalid model JSON, wrong IDs, fabricated quotes, and detected secrets produce a blocked result.

## What the receipt means

`passed` means a particular deterministic check succeeded. It does not mean the answer is factually correct. An exact quote can be real while the claim misinterprets it. The current evaluation set is a small regression fixture, not an independent benchmark.

## Next quality increments

1. Add a labeled domain dataset with answerability, source spans, and adversarial cases.
2. Measure retrieval recall, supported-claim rate, abstention precision, latency, and cost separately for each configured model.
3. Add a second semantic verifier and calibrate it against human labels. Keep deterministic gates as the final release authority.
4. If external actions are added, give each tool an allowlisted scope, a dry-run preview, an explicit approval state, and an audit receipt.
