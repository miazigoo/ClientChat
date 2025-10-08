import asyncio
import json
import random
import threading
from datetime import datetime
from websockets.server import serve


OPERATORS = ["Петрова Аня", "Сидоров Михаил", "Головач Лена"]

def now_iso() -> str:
    return datetime.utcnow().isoformat()

class ChatServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self._rooms = {}  # room -> set of websockets
        self._lock = asyncio.Lock()
        self._thread = None

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

    async def _operator_reply(self, room: str, dialog_id: str):
        await asyncio.sleep(random.uniform(1.0, 2.5))
        reply_texts = [
            "Спасибо за обращение! Сейчас разберемся.",
            "Передаю ваш запрос специалисту. Ожидайте, пожалуйста.",
            "Проверяю информацию, одну минуту.",
            "Попробуйте, пожалуйста, обновить приложение и повторить действие.",
        ]
        payload = {
            "type": "message",
            "room": room,
            "dialog_id": dialog_id,
            "sender": "operator",
            "operator_name": random.choice(OPERATORS),
            "text": random.choice(reply_texts),
            "ts": now_iso(),
        }
        await self._broadcast(room, payload)

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

                elif data.get("type") == "message":
                    room = data.get("room")
                    if not room:
                        continue
                    # Рассылаем сообщение всем подписанным
                    await self._broadcast(room, data)
                    # Если это юзер — эмулируем ответ оператора
                    if data.get("sender") == "user":
                        dialog_id = data.get("dialog_id")
                        asyncio.create_task(self._operator_reply(room, dialog_id))

        finally:
            # Очистим подписки при закрытии
            async with self._lock:
                for conns in self._rooms.values():
                    conns.discard(ws)

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
