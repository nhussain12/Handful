from __future__ import annotations

import asyncio
import json
import logging
import os

from pathlib import Path

# Point Python's TLS at certifi's CA bundle. Without this, the uv-managed Python on
# macOS has no trusted root certs and the outbound connection to Deepgram fails with
# "CERTIFICATE_VERIFY_FAILED". Must run before any SSL connection is made.
import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("SSL_CERT_DIR", os.path.dirname(certifi.where()))

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse

from .agent_manager import AgentSession

load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(title="Handful", version="0.1.0")

API_KEY = os.getenv("DEEPGRAM_API_KEY", "")

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/")
async def index() -> HTMLResponse:
    html = STATIC_DIR.joinpath("index.html").read_text()
    return HTMLResponse(html)


# Frontend assets referenced by index.html as relative URLs (./support.js, hero.png, …).
@app.get("/support.js")
async def support_js():
    return FileResponse(STATIC_DIR / "support.js", media_type="application/javascript")


@app.get("/hero.png")
async def hero_png():
    return FileResponse(STATIC_DIR / "hero.png", media_type="image/png")


@app.get("/ingredients.png")
async def ingredients_png():
    return FileResponse(STATIC_DIR / "ingredients.png", media_type="image/png")

@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "handful"}


@app.get("/notes")
async def list_notes() -> list[dict]:
    import glob as glob_mod
    files = glob_mod.glob("notes/*.txt")
    result = []
    for f in sorted(files, reverse=True)[:20]:
        text = open(f).read()
        result.append({"filename": f, "preview": text[:200]})
    return result


@app.websocket("/converse")
async def converse(websocket: WebSocket) -> None:
    await websocket.accept()
    logger.info("Client connected")

    async def client_send(data: str | bytes) -> None:
        if isinstance(data, bytes):
            await websocket.send_bytes(data)
        else:
            await websocket.send_text(data)

    session = AgentSession(client_send=client_send)

    media_queue: asyncio.Queue[bytes] = asyncio.Queue()

    async def read_client():
        try:
            while True:
                msg = await websocket.receive()
                if msg.get("type") == "websocket.disconnect":
                    break
                if msg.get("type") == "websocket.receive":
                    raw = msg.get("bytes") or msg.get("text")
                    if isinstance(raw, bytes):
                        await media_queue.put(raw)
                    elif isinstance(raw, str):
                        try:
                            cmd = json.loads(raw)
                            await handle_client_command(session, cmd)
                        except json.JSONDecodeError:
                            pass
        except WebSocketDisconnect:
            pass
        except Exception as exc:
            logger.debug(f"Client reader ended: {exc}")

    SILENCE = b'\x00' * 3840

    async def media_iter():
        while True:
            try:
                yield await asyncio.wait_for(media_queue.get(), timeout=0.1)
            except asyncio.TimeoutError:
                yield SILENCE

    reader_task = asyncio.create_task(read_client())

    try:
        await session.run(api_key=API_KEY, client_media_iter=media_iter())
    except Exception as exc:
        logger.error(f"Session error: {exc}")
    finally:
        reader_task.cancel()
        logger.info("Client disconnected")


async def handle_client_command(session: AgentSession, cmd: dict) -> None:
    cmd_type = cmd.get("type", "")

    if cmd_type == "get_recipe_state":
        state = session.recipe.get_state()
        if session._agent:
            from deepgram.agent.v1.types import AgentV1InjectUserMessage
            msg = AgentV1InjectUserMessage(
                type="InjectUserMessage",
                content=f"[System: User requested current recipe state. State: {json.dumps(state)}]",
            )
            await session._agent.send_inject_user_message(msg)

    elif cmd_type == "get_timers":
        timers = session.timers.get_active_timers()
        await session._send_to_client({"type": "timer_update", "timers": timers})

    elif cmd_type == "cancel_timer":
        label = cmd.get("label", "")
        result = await session.timers.cancel_timer(label)
        await session._send_to_client({"type": "timer_cancelled", "result": result})

    elif cmd_type == "inject_speech":
        text = cmd.get("text", "")
        if session._agent and text:
            from deepgram.agent.v1.types import AgentV1InjectUserMessage
            msg = AgentV1InjectUserMessage(
                type="InjectUserMessage",
                content=text,
            )
            await session._agent.send_inject_user_message(msg)
