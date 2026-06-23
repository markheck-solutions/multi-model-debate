"""FastAPI server for the local and hosted GUI lanes."""

from __future__ import annotations

import asyncio
import webbrowser
from pathlib import Path

import uvicorn
from fastapi import APIRouter, FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from multi_model_debate import __version__
from multi_model_debate.local_app.demo_data import (
    build_default_panel,
    build_demo_accounts,
    build_demo_events,
    build_demo_models,
    create_demo_run,
)
from multi_model_debate.local_app.schemas import (
    CatalogResponse,
    DebateRunRequest,
    DebateRunSummary,
    HealthResponse,
    ProviderAccount,
    RunStatus,
)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
LOCAL_ORIGINS = (
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:8787",
    "http://localhost:8787",
)


class LocalAppState:
    """In-memory state for demo/local app sessions."""

    def __init__(self) -> None:
        self.accounts = build_demo_accounts()
        self.models = build_demo_models()
        self.default_panel = build_default_panel()
        self.runs: dict[str, DebateRunSummary] = {}

    def create_run(self, request: DebateRunRequest) -> DebateRunSummary:
        """Create a demo run summary and save it in memory."""
        run = create_demo_run(question=request.question, panel=request.panel)
        self.runs[run.id] = run
        return run

    def get_run(self, run_id: str) -> DebateRunSummary:
        """Return a run or raise a user-safe 404."""
        if run_id not in self.runs:
            raise HTTPException(status_code=404, detail="Run not found.")
        return self.runs[run_id]

    def cancel_run(self, run_id: str) -> DebateRunSummary:
        """Mark a run cancelled unless it already completed."""
        run = self.get_run(run_id)
        if run.status is RunStatus.COMPLETED:
            return run
        cancelled = run.model_copy(update={"status": RunStatus.CANCELLED})
        self.runs[run_id] = cancelled
        return cancelled


class LocalAppRoutes:
    """HTTP and WebSocket route handlers for the local GUI API."""

    def __init__(self, state: LocalAppState) -> None:
        self.state = state

    def router(self) -> APIRouter:
        """Build API routes without mixing them into app construction."""
        router = APIRouter(prefix="/api")
        router.add_api_route("/health", self.health, methods=["GET"], response_model=HealthResponse)
        router.add_api_route(
            "/accounts",
            self.accounts,
            methods=["GET"],
            response_model=list[ProviderAccount],
        )
        router.add_api_route(
            "/models", self.catalog, methods=["GET"], response_model=CatalogResponse
        )
        router.add_api_route(
            "/runs",
            self.create_run,
            methods=["POST"],
            response_model=DebateRunSummary,
        )
        router.add_api_route(
            "/runs",
            self.list_runs,
            methods=["GET"],
            response_model=list[DebateRunSummary],
        )
        router.add_api_route(
            "/runs/{run_id}",
            self.get_run,
            methods=["GET"],
            response_model=DebateRunSummary,
        )
        router.add_api_route(
            "/runs/{run_id}/cancel",
            self.cancel_run,
            methods=["POST"],
            response_model=DebateRunSummary,
        )
        router.add_api_route(
            "/runs/{run_id}/artifacts/final",
            self.final_report,
            methods=["GET"],
            response_model=str,
        )
        router.add_api_websocket_route("/runs/{run_id}/events", self.run_events)
        return router

    def health(self) -> HealthResponse:
        """Return local runner health."""
        return HealthResponse(status="ok", version=__version__, lane="local")

    def accounts(self) -> list[ProviderAccount]:
        """Return non-secret provider metadata."""
        return self.state.accounts

    def catalog(self) -> CatalogResponse:
        """Return account, model, and default panel choices."""
        return CatalogResponse(
            accounts=self.state.accounts,
            models=self.state.models,
            default_panel=self.state.default_panel,
        )

    def create_run(self, request: DebateRunRequest) -> DebateRunSummary:
        """Create a demo run."""
        return self.state.create_run(request)

    def list_runs(self) -> list[DebateRunSummary]:
        """Return run history for the current session."""
        return list(self.state.runs.values())

    def get_run(self, run_id: str) -> DebateRunSummary:
        """Return one run by id."""
        return self.state.get_run(run_id)

    def cancel_run(self, run_id: str) -> DebateRunSummary:
        """Cancel a running run."""
        return self.state.cancel_run(run_id)

    def final_report(self, run_id: str) -> str:
        """Return final report markdown for a run."""
        run = self.state.get_run(run_id)
        return run.final_report or ""

    async def run_events(self, websocket: WebSocket, run_id: str) -> None:
        """Stream demo events over WebSocket."""
        self.state.get_run(run_id)
        await websocket.accept()
        for event in build_demo_events(run_id):
            await websocket.send_json(event.model_dump(mode="json"))
            await asyncio.sleep(0.05)
        await websocket.close()


def create_app(static_dir: Path | None = None) -> FastAPI:
    """Create the local GUI FastAPI app."""
    app = FastAPI(title="Multi-Model Debate", version=__version__)
    state = LocalAppState()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(LOCAL_ORIGINS),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(LocalAppRoutes(state).router())

    if static_dir and (static_dir / "index.html").exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="web")

    return app


def serve_app(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    static_dir: Path | None = None,
    open_browser: bool = True,
) -> None:
    """Run the local GUI server."""
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("The GUI runner only binds to localhost by default.")

    url = f"http://{host}:{port}"
    if open_browser:
        webbrowser.open(url)

    uvicorn.run(create_app(static_dir=static_dir), host=host, port=port)
