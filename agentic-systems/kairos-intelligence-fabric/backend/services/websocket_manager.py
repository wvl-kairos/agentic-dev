from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.append(ws)
        logger.info("WebSocket connected (%d total)", len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self._connections:
            self._connections.remove(ws)
        logger.info("WebSocket disconnected (%d remaining)", len(self._connections))

    async def send_chunk(self, ws: WebSocket, chunk_type: str, data: str) -> None:
        """Send a typed chunk to a specific WebSocket."""
        try:
            await ws.send_json({"type": chunk_type, "data": data})
        except Exception as e:
            logger.warning("Failed to send chunk: %s", e)

    async def send_json(self, ws: WebSocket, data: Any) -> None:
        try:
            await ws.send_json(data)
        except Exception as e:
            logger.warning("Failed to send JSON: %s", e)

    async def stream_text(self, ws: WebSocket, text: str, chunk_size: int = 20) -> None:
        """Stream text in small chunks to simulate typing."""
        words = text.split()
        buffer = []
        for word in words:
            buffer.append(word)
            if len(buffer) >= chunk_size:
                await self.send_chunk(ws, "content", " ".join(buffer) + " ")
                buffer = []
        if buffer:
            await self.send_chunk(ws, "content", " ".join(buffer))


ws_manager = ConnectionManager()
