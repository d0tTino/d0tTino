from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio


from llm.router import send_prompt
from scripts.thm import apply_palette, REPO_ROOT
from scripts import ai_exec

STATE_PATH = Path(os.environ.get("API_STATE_PATH", REPO_ROOT / "api_state.json"))


def _load_state() -> dict[str, Any]:
    if STATE_PATH.exists():
        with STATE_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {"queries": 0, "nodes": [], "edges": []}


def _save_state(state: dict[str, Any]) -> None:
    STATE_PATH.write_text(json.dumps(state), encoding="utf-8")


def record_prompt(prompt: str) -> None:
    state = _load_state()
    state["queries"] += 1
    node_id = state["queries"]
    state["nodes"].append({"id": node_id, "text": prompt})
    if node_id > 1:
        state["edges"].append({"source": node_id - 1, "target": node_id})
    _save_state(state)


def get_stats() -> dict[str, int]:
    state = _load_state()
    return {"queries": state["queries"], "memory": len(state["nodes"])}


def get_graph() -> dict[str, list]:
    state = _load_state()
    return {"nodes": state["nodes"], "edges": state["edges"]}

app = FastAPI()
UME_API_URL = os.environ.get("UME_API_URL", "http://localhost:8000")

class PromptRequest(BaseModel):
    prompt: str
    local: bool = False

class PaletteRequest(BaseModel):
    name: str

class ExecRequest(BaseModel):
    goal: str

@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/api/prompt")
async def prompt(req: PromptRequest) -> dict[str, str]:
    record_prompt(req.prompt)
    result = send_prompt(req.prompt, local=req.local)
    return {"response": result}

@app.post("/api/palette")
async def palette(req: PaletteRequest) -> dict[str, str]:
    apply_palette(req.name, REPO_ROOT)
    return {"status": "applied"}

@app.post("/api/plan")
async def plan(req: ExecRequest) -> dict[str, list[str]]:
    steps = ai_exec.plan(req.goal)
    return {"steps": steps}

@app.get("/api/exec")
async def exec_stream(goal: str):
    steps = ai_exec.plan(goal)

    async def streamer():
        for step in steps:
            yield f"data: $ {step}\n\n"
            proc = await asyncio.create_subprocess_shell(
                step,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            assert proc.stdout is not None
            async for line in proc.stdout:
                yield f"data: {line.decode().rstrip()}\n\n"
            await proc.wait()
            yield f"data: (exit {proc.returncode})\n\n"

    return StreamingResponse(streamer(), media_type="text/event-stream")

@app.get("/api/stats")
async def stats() -> dict[str, int]:
    return get_stats()

@app.get("/api/graph")
async def graph() -> dict[str, list]:
    return get_graph()


if __name__ == "__main__":  # pragma: no cover - manual launch
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

__all__ = [
    "app",
    "record_prompt",
    "get_stats",
    "get_graph",
    "plan",
    "exec_stream",
]
