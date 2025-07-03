from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from scripts.ai_router import send_prompt
from scripts.thm import apply_palette, REPO_ROOT

app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str
    local: bool = False

class PaletteRequest(BaseModel):
    name: str

@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/api/prompt")
async def prompt(req: PromptRequest) -> dict[str, str]:
    result = send_prompt(req.prompt, local=req.local)
    return {"response": result}

@app.post("/api/palette")
async def palette(req: PaletteRequest) -> dict[str, str]:
    apply_palette(req.name, REPO_ROOT)
    return {"status": "applied"}

@app.get("/api/stats")
async def stats() -> dict[str, int]:
    return {"queries": 0, "memory": 0}

@app.get("/api/graph")
async def graph() -> dict[str, list]:
    return {"nodes": [], "edges": []}

if __name__ == "__main__":  # pragma: no cover - manual launch
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

__all__ = ["app"]
