"""
MCP (Model Context Protocol) Server - Python

Features:
- HTTP JSON MCP endpoint (/mcp) for request/response model interactions
- WebSocket MCP endpoint (/mcp/ws) for streaming/multiplexed sessions
- In-memory session store with configurable max context tokens per session
- Tool integrations: directory listing and nmap (whitelisted targets/paths)
- Simple "LLM" adapter placeholder (echo / system injection) — replace with real model call
- Safety: strict ALLOWED_TARGETS and ALLOWED_PATHS; timeouts and output limits

WARNING: This server can run system commands (nmap). Only run in safe/test environments and
configure ALLOWED_TARGETS carefully. Do NOT expose to untrusted networks without auth and rate-limiting.

Dependencies:
    pip install fastapi uvicorn python-multipart websockets
    (nmap binary must be installed for nmap tool)

Run:
    uvicorn mcp_server:app --host 0.0.0.0 --port 8080

API examples:
POST /mcp
{
  "session_id": "sess1",
  "instruction": "Summarize: Hello world",
  "tools": [],
  "max_tokens": 1024
}

WebSocket /mcp/ws
Send/receive JSON messages for low-latency streaming.
"""

import asyncio
import json
import shlex
import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from ipaddress import ip_address, ip_network
import subprocess

# ---------------- Configuration ----------------
ALLOWED_TARGETS = ["127.0.0.1/32", "::1/128"]  # CIDR ranges for nmap
ALLOWED_PATHS = ["/tmp", "/var/www", "."]    # directories allowed for listing
MAX_CONTEXT_TOKENS = 16384
NMAP_OUTPUT_LIMIT = 200_000
SUBPROCESS_TIMEOUT = 25

# Simple token counting heuristic (not exact tokens)
def count_tokens(text: str) -> int:
    return max(1, len(text.split()))

# Pre-parse allowed networks
ALLOWED_NETWORKS = [ip_network(x) for x in ALLOWED_TARGETS]

# ---------------- Session Store ----------------
class Session:
    def __init__(self, session_id: str, max_tokens: int = MAX_CONTEXT_TOKENS):
        self.session_id = session_id
        self.history: List[Dict[str, Any]] = []  # list of {role, content}
        self.max_tokens = max_tokens
        self.token_count = 0

    def append(self, role: str, content: str):
        t = count_tokens(content)
        self.history.append({"role": role, "content": content})
        self.token_count += t
        # truncate if over budget (simple drop oldest)
        while self.token_count > self.max_tokens and self.history:
            removed = self.history.pop(0)
            self.token_count -= count_tokens(removed.get("content", ""))

    def to_dict(self):
        return {"session_id": self.session_id, "history": self.history, "token_count": self.token_count}

SESSIONS: Dict[str, Session] = {}

# ---------------- FastAPI app ----------------
app = FastAPI(title="MCP Server")

# ---------------- Pydantic models ----------------
class MCPRequest(BaseModel):
    session_id: Optional[str]
    instruction: str
    tools: Optional[List[str]] = []
    max_tokens: Optional[int] = MAX_CONTEXT_TOKENS

class MCPResponse(BaseModel):
    session_id: str
    reply: str
    used_tools: Optional[List[str]] = []
    session: Optional[Dict[str, Any]] = None

# ---------------- Utility functions ----------------
def is_target_allowed(target: str) -> bool:
    try:
        ip = ip_address(target)
    except Exception:
        return False
    for net in ALLOWED_NETWORKS:
        if ip in net:
            return True
    return False

def is_path_allowed(path: str) -> bool:
    # Resolve and check that path is inside one of allowed roots
    try:
        real = os.path.realpath(path)
    except Exception:
        return False
    for root in ALLOWED_PATHS:
        if real.startswith(os.path.realpath(root)):
            return True
    return False

async def run_nmap(target: str) -> str:
    if not is_target_allowed(target):
        return f"Target not allowed: {target}\n"
    cmd = ["nmap", "-sV", "--reason", target]
    try:
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=SUBPROCESS_TIMEOUT)
        except asyncio.TimeoutError:
            proc.kill()
            return f"nmap timed out after {SUBPROCESS_TIMEOUT}s\n"
        out = stdout[:NMAP_OUTPUT_LIMIT].decode("utf-8", errors="replace")
        if len(stdout) > NMAP_OUTPUT_LIMIT:
            out += "\n---output truncated---\n"
        if stderr:
            out += "\n[nmap stderr]\n" + stderr.decode("utf-8", errors="replace")
        return out
    except FileNotFoundError:
        return "nmap not installed on server\n"
    except Exception as e:
        return f"nmap failed: {e}\n"

def list_directory(path: str) -> str:
    if not is_path_allowed(path):
        return f"Path not allowed: {path}\n"
    if not os.path.exists(path):
        return f"Not found: {path}\n"
    if not os.path.isdir(path):
        return f"Not a directory: {path}\n"
    try:
        items = []
        with os.scandir(path) as it:
            for e in it:
                typ = 'DIR' if e.is_dir() else 'FILE'
                size = e.stat().st_size if e.is_file() else ''
                items.append(f"{typ:4} {e.name} {size}")
        return "\n".join(items) + "\n"
    except Exception as e:
        return f"ls failed: {e}\n"

# ---------------- LLM Adapter (placeholder) ----------------
# Replace with real model calls (Hugging Face, OpenAI, local LLM, etc.)
# This simple adapter echoes the instruction and uses session history.
async def llm_generate(session: Session, instruction: str, max_tokens: int) -> str:
    # Example of simple system behavior injection
    system_prompt = "You are MCP assistant. Keep replies short."
    # Build prompt from history (naive concatenation)
    prompt_parts = [system_prompt]
    for h in session.history:
        prompt_parts.append(f"{h['role']}: {h['content']}")
    prompt_parts.append(f"user: {instruction}")
    prompt = "\n".join(prompt_parts)
    # Simulate generation
    await asyncio.sleep(0.01)  # placeholder latency
    reply = f"[Echo] {instruction}"
    return reply

# ---------------- HTTP MCP endpoint ----------------
@app.post("/mcp", response_model=MCPResponse)
async def mcp_endpoint(req: MCPRequest):
    sid = req.session_id or "default"
    if sid not in SESSIONS:
        SESSIONS[sid] = Session(sid, max_tokens=req.max_tokens or MAX_CONTEXT_TOKENS)
    session = SESSIONS[sid]

    # Append user instruction to session history
    session.append("user", req.instruction)

    used_tools = []
    # Tool handling: simple syntax: tools list contains strings like "nmap:1.2.3.4" or "ls:/path"
    tool_results = []
    for t in req.tools or []:
        if t.startswith("nmap:"):
            target = t.split(":", 1)[1]
            res = await run_nmap(target)
            tool_results.append({"tool": "nmap", "target": target, "output": res})
            used_tools.append("nmap")
            session.append("tool", f"nmap {target} -> {res[:1000]}")
        elif t.startswith("ls:"):
            path = t.split(":", 1)[1]
            res = list_directory(path)
            tool_results.append({"tool": "ls", "path": path, "output": res})
            used_tools.append("ls")
            session.append("tool", f"ls {path} -> {res[:1000]}")
        else:
            tool_results.append({"tool": "unknown", "spec": t, "output": "unsupported"})

    # Call LLM adapter
    reply = await llm_generate(session, req.instruction, req.max_tokens or MAX_CONTEXT_TOKENS)
    session.append("assistant", reply)

    # Build response
    resp = MCPResponse(session_id=sid, reply=reply, used_tools=used_tools, session=session.to_dict())
    return resp

# ---------------- WebSocket MCP endpoint ----------------
class ConnectionManager:
    def __init__(self):
        self.active: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active:
            del self.active[client_id]

    async def send_json(self, client_id: str, data: Dict[str, Any]):
        ws = self.active.get(client_id)
        if ws:
            await ws.send_json(data)

manager = ConnectionManager()

@app.websocket("/mcp/ws")
async def mcp_ws(websocket: WebSocket):
    # Expect initial message to include session_id
    await websocket.accept()
    try:
        init = await websocket.receive_text()
        obj = json.loads(init)
        sid = obj.get("session_id", "default")
        client_id = f"ws:{sid}:{id(websocket)}"
        await manager.connect(websocket, client_id)
        if sid not in SESSIONS:
            SESSIONS[sid] = Session(sid)
        session = SESSIONS[sid]

        # A simple loop: receive JSON messages {"instruction":..., "tools": [...]} and respond
        while True:
            text = await websocket.receive_text()
            msg = json.loads(text)
            instruction = msg.get("instruction", "")
            tools = msg.get("tools", [])

            session.append("user", instruction)

            used_tools = []
            tool_results = []
            for t in tools:
                if t.startswith("nmap:"):
                    target = t.split(":", 1)[1]
                    res = await run_nmap(target)
                    tool_results.append({"tool": "nmap", "target": target, "output": res})
                    used_tools.append("nmap")
                    session.append("tool", f"nmap {target} -> {res[:1000]}")
                elif t.startswith("ls:"):
                    path = t.split(":", 1)[1]
                    res = list_directory(path)
                    tool_results.append({"tool": "ls", "path": path, "output": res})
                    used_tools.append("ls")
                    session.append("tool", f"ls {path} -> {res[:1000]}")

            # generate reply (could stream in chunks)
            reply = await llm_generate(session, instruction, MAX_CONTEXT_TOKENS)
            session.append("assistant", reply)

            out = {"session_id": sid, "reply": reply, "used_tools": used_tools}
            await manager.send_json(client_id, out)

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        try:
            await websocket.send_json({"error": str(e)})
        except Exception:
            pass
        manager.disconnect(client_id)

# ---------------- Admin endpoints ----------------
@app.get("/session/{session_id}")
async def get_session(session_id: str):
    s = SESSIONS.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="session not found")
    return JSONResponse(content=s.to_dict())

@app.get("/sessions")
async def list_sessions():
    return JSONResponse(content={k: v.to_dict() for k, v in SESSIONS.items()})

# ---------------- Simple health check ----------------
@app.get("/ping")
async def ping():
    return {"ok": True}
