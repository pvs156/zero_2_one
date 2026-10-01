"use client";

import { FormEvent, useState } from "react";

type Source = { source_id: string; title: string; quote: string; score: number };
type GateCheck = { name: string; passed: boolean; detail: string };
type Answer = {
  status: "answered" | "abstained" | "blocked";
  answer: string;
  sources: Source[];
  checks: GateCheck[];
  mode: "offline" | "claude";
};

const prompts = [
  "How long is the return window?",
  "When do customers receive a tracking link?",
  "How can customers request account deletion?",
];

export default function Home() {
  const [question, setQuestion] = useState(prompts[0]);
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setAnswer(null);
    try {
      const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
      const response = await fetch(`${base}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!response.ok) throw new Error(`API returned ${response.status}`);
      setAnswer((await response.json()) as Answer);
    } catch {
      setError("Could not reach the API. Start the Python service on port 8000 and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand"><span className="brandmark">G</span> GroundedGate</div>
        <span className="eyebrow">Evidence first agent lab</span>
      </header>

      <section className="hero">
        <div className="hero-tag">ANSWER QUALITY, VISIBLE</div>
        <h1>Answers should earn<br /><em>their confidence.</em></h1>
        <p>Ask a question about the sample documents. GroundedGate retrieves evidence, drafts a response, and runs deterministic checks before anything is shown.</p>
      </section>

      <div className="workspace">
        <section className="panel ask-panel">
          <div className="panel-heading"><span>01 / ASK</span><span>Sample corpus</span></div>
          <form onSubmit={submit}>
            <label htmlFor="question">Your question</label>
            <textarea id="question" value={question} onChange={(event) => setQuestion(event.target.value)} minLength={3} maxLength={500} required />
            <button type="submit" disabled={loading}>{loading ? "Checking evidence…" : "Run quality gates →"}</button>
          </form>
          <div className="suggestions">
            <span>TRY A QUESTION</span>
            {prompts.map((prompt) => <button type="button" key={prompt} onClick={() => setQuestion(prompt)}>{prompt}</button>)}
          </div>
        </section>

        <section className="panel result-panel" aria-live="polite">
          <div className="panel-heading"><span>02 / RESULT</span><span>{answer?.mode === "claude" ? "Claude mode" : "Offline demo"}</span></div>
          {error && <p className="error">{error}</p>}
          {!answer && !error && <div className="empty"><span className="empty-icon">◇</span><h2>Evidence appears here</h2><p>Run a question to inspect the answer, source quotes, and every gate result.</p></div>}
          {answer && <>
            <div className={`status ${answer.status}`}>{answer.status.toUpperCase()}</div>
            <p className="answer">{answer.answer}</p>
            <h3>Evidence</h3>
            {answer.sources.length === 0 ? <p className="muted">No source was published for this result.</p> : answer.sources.map((source) => (
              <article className="source" key={`${source.source_id}-${source.quote}`}>
                <div><strong>{source.title}</strong><code>{source.source_id}</code></div>
                <blockquote>{source.quote}</blockquote>
              </article>
            ))}
            <h3>Validation receipt</h3>
            <div className="checks">{answer.checks.map((check) => (
              <div className="check" key={check.name}>
                <span className={check.passed ? "pass" : "fail"}>{check.passed ? "✓" : "×"}</span>
                <div><strong>{check.name.replaceAll("_", " ")}</strong><small>{check.detail}</small></div>
              </div>
            ))}</div>
          </>}
        </section>
      </div>

      <footer>GroundedGate is a demonstration. Exact quote checks verify source matching, not semantic truth.</footer>
    </main>
  );
}
