#!/usr/bin/env python3
# Single-URL OpenAI-compatible router for multiple llama.cpp servers
# Usage:
#   python openai_router.py --host 127.0.0.1 --port 9000 --config router_config.json
#
# router_config.json format:
# {
#   "routes": {
#     "Qwen3-8B-Q8_0.gguf": "http://127.0.0.1:8081/v1",
#     "gemma-3-4b-it-q4_0.gguf": "http://127.0.0.1:8082/v1"
#   }
# }

import argparse, json
from typing import Dict, Any
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
import uvicorn

app = FastAPI()
ROUTES: Dict[str, str] = {}  # model -> base_url (…/v1)

def _pick_base(model: str) -> str:
    base = ROUTES.get(model)
    if not base:
        raise HTTPException(status_code=404, detail=f"Unknown model '{model}'. Known: {list(ROUTES.keys())}")
    return base

async def _aggregate_models() -> Dict[str, Any]:
    out = {"object": "list", "data": []}
    seen = set()
    async with httpx.AsyncClient(timeout=15.0) as client:
        for base in set(ROUTES.values()):
            try:
                r = await client.get(f"{base}/models")
                r.raise_for_status()
                data = r.json().get("data", [])
                for m in data:
                    mid = m.get("id")
                    if mid and mid not in seen:
                        out["data"].append(m); seen.add(mid)
            except Exception:
                pass
    return out

async def _forward_json(req: Request, path: str, streamable: bool = False) -> Response:
    body = await req.json()
    model = body.get("model")
    if not model:
        raise HTTPException(status_code=400, detail="Missing 'model' in request body")
    base = _pick_base(model)
    url = f"{base}{path}"

    # pass through minimal headers if you want (auth is typically ignored locally)
    headers = {}
    # for k, v in req.headers.items(): headers[k] = v

    if streamable and bool(body.get("stream")):
        # *** Streaming path (SSE) ***
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", url, json=body, headers=headers) as upstream:
                # Propagate status; use event-stream
                async def agen():
                    async for chunk in upstream.aiter_bytes():
                        if chunk:
                            yield chunk
                return StreamingResponse(
                    agen(),
                    status_code=upstream.status_code,
                    media_type="text/event-stream",
                    headers={"Cache-Control": "no-cache"},
                )
    else:
        # *** Non-streaming path ***
        async with httpx.AsyncClient(timeout=None) as client:
            r = await client.post(url, json=body, headers=headers)
            # Try to preserve Content-Type; default to application/json
            ctype = r.headers.get("content-type", "application/json")
            # If it looks like JSON but isn't strictly labelled, fix it for the client:
            try:
                # If upstream returned text/plain but contains JSON, normalize it:
                if "application/json" not in ctype and r.text and r.text.strip().startswith("{"):
                    return JSONResponse(status_code=r.status_code, content=r.json())
            except Exception:
                pass
            return Response(content=r.content, status_code=r.status_code, media_type=ctype)

@app.get("/v1/models")
async def list_models():
    return await _aggregate_models()

@app.post("/v1/chat/completions")
async def chat(req: Request):
    return await _forward_json(req, "/chat/completions", streamable=True)

@app.post("/v1/completions")
async def completions(req: Request):
    return await _forward_json(req, "/completions", streamable=True)

@app.post("/v1/embeddings")
async def embeddings(req: Request):
    return await _forward_json(req, "/embeddings", streamable=False)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=9000)
    ap.add_argument("--config", required=True, help="router_config.json")
    args = ap.parse_args()

    global ROUTES
    with open(args.config, "r", encoding="utf-8") as f:
        ROUTES = json.load(f)["routes"]

    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
