"""FastAPI surface for the GroundedGate demo."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from groundedgate.schemas import AnswerResponse, AskRequest
from groundedgate.service import AgentService

DEFAULT_DOCS = Path(__file__).resolve().parents[2] / "data" / "knowledge"


def create_app(service: AgentService | None = None) -> FastAPI:
    """Create an API bound to a fixed local document corpus."""
    docs = Path(os.getenv("GROUNDEDGATE_DOCS_DIR", str(DEFAULT_DOCS)))
    agent = service or AgentService.from_directory(docs)
    app = FastAPI(title="GroundedGate", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.get("/health")
    def health() -> dict[str, str | int]:
        return {"status": "ok", "passages": len(agent.passages), "mode": agent.generator.mode}

    @app.get("/documents")
    def documents() -> list[str]:
        return sorted({passage.title for passage in agent.passages})

    @app.post("/ask", response_model=AnswerResponse)
    def ask(payload: AskRequest) -> AnswerResponse:
        return agent.ask(payload.question)

    return app


app = create_app()
