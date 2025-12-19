import asyncio
from collections import deque
from typing import Set
from fastapi import WebSocket

# Store connected clients
connected_clients: Set[WebSocket] = set()

# Store recent logs (last 100)
log_buffer: deque = deque(maxlen=100)


async def broadcast_log(message: str):
    """Send log message to all connected WebSocket clients."""
    log_buffer.append(message)

    disconnected = set()
    for client in connected_clients:
        try:
            await client.send_text(message)
        except Exception:
            disconnected.add(client)

    # Remove disconnected clients
    for client in disconnected:
        connected_clients.discard(client)


def log(message: str, terminal: bool = False):
    """Log a message and broadcast to clients. Safe to call from sync or async context."""
    if terminal:
        print(message)

    # Add to buffer immediately (sync safe)
    log_buffer.append(message)

    # Try to broadcast to WebSocket clients
    try:
        loop = asyncio.get_running_loop()
        # We're in an async context, create task
        loop.create_task(broadcast_log(message))
    except RuntimeError:
        # No running event loop - that's okay, message is in buffer
        # Will be sent when clients connect and receive buffer
        pass


async def handle_websocket(websocket: WebSocket):
    """Handle WebSocket connection for log streaming."""
    await websocket.accept()
    connected_clients.add(websocket)

    # Send recent logs to new client
    for msg in log_buffer:
        await websocket.send_text(msg)

    try:
        while True:
            # Keep connection alive, wait for client messages (like ping)
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        connected_clients.discard(websocket)
