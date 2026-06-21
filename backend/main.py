"""Handful — FastAPI server for hands-free cooking assistant.

Run with:
    uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

WebSocket endpoint: ws://localhost:8000/converse
Health check:       http://localhost:8000/health
"""

import logging

import uvicorn

from handful.server import app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
