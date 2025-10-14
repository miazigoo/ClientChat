import asyncio
import json
import threading
from datetime import datetime
from websockets.server import serve
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError


def now_iso() -> str:
    return datetime.utcnow().isoformat()

class ChatServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self._rooms = {}  # room -> set of websockets
        self._lock = asyncio.Lock()
        self._thread = None
        self._agents = {}   # ws -> {"instance_id":..., "operator_id":...}

    async def _broadcast(self, room: str, payload: dict):
        msg = json.dumps(payload, ensure_ascii=False)
        conns = list(self._rooms.get(room, set()))
        to_remove = []
        for ws in conns:
            try:
                await ws.send(msg)
            except Exception:
                to_remove.append(ws)
        if to_remove:
            async with self._lock:
                for ws in to_remove:
                    self._rooms.get(room, set()).discard(ws)

    async def _handler(self, ws):
        # При подключении клиент может подписываться на комнаты: {"type":"subscribe","room":"dialog:XYZ"}
        try:
            async for raw in ws:
                try:
                    data = json.loads(raw)
                except Exception:
                    continue

                if data.get("type") == "subscribe":
                    room = data.get("room")
                    if not room:
                        continue
                    async with self._lock:
                        self._rooms.setdefault(room, set()).add(ws)

                elif data.get("type") == "hello":
                    ag = data.get("agent") or {}
                    self._agents[ws] = {
                        "instance_id": ag.get("instance_id"),
                        "operator_id": ag.get("operator_id"),
                    }
                    # Ответим ack только этому ws
                    try:
                        await ws.send(json.dumps({"type": "hello_ack", "ts": now_iso(), "agent": self._agents[ws]},
                                                 ensure_ascii=False))
                    except (ConnectionClosedOK, ConnectionClosedError):
                        pass

                elif data.get("type") == "start_chat":
                    room = data.get("room")
                    if not room:
                        continue

                    async with self._lock:
                        self._rooms.setdefault(room, set()).add(ws)

                    agent = self._agents.get(ws, {})

                    try:
                        await ws.send(json.dumps({
                            "type": "start_chat_ack",
                            "room": room,
                            "dialog_id": data.get("dialog_id"),
                            "user_id": data.get("user_id"),
                            "agent": agent,
                            "ts": now_iso(),
                        }, ensure_ascii=False))
                    except (ConnectionClosedOK, ConnectionClosedError):
                        pass

                    await self._broadcast(room, {
                        "type": "system", "room": room, "dialog_id": data.get("dialog_id"),
                        "text": "Чат инициирован агентом", "agent": agent, "ts": now_iso(),
                    })

                elif data.get("type") == "message":
                    room = data.get("room")
                    if not room:
                        continue
                    # Просто пересылаем сообщение всем участникам комнаты
                    await self._broadcast(room, data)

        finally:
            async with self._lock:
                for conns in self._rooms.values():
                    conns.discard(ws)
                self._agents.pop(ws, None)

    async def _run(self):
        async with serve(self._handler, self.host, self.port):
            # Работаем, пока жив event loop
            await asyncio.Future()

    def start_in_background(self):
        # Запускаем сервер в отдельном потоке
        def runner():
            asyncio.run(self._run())

        self._thread = threading.Thread(target=runner, daemon=True)
        self._thread.start()
