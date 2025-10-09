import asyncio
import json
import threading
from typing import Optional
from PySide6.QtCore import QObject, Signal
import websockets


class ChatClient(QObject):
    """
    Channels-совместимый WS-клиент.
    Подключается к конкретной комнате: ws://host/ws/chat/{room_id}/?token=JWT
    Получает события:
      - {"type":"new_message","message":{...}}
      - {"type":"room_update","room":{...}}
    Отправка сообщений по WS опциональна (у нас отправка идёт через HTTP).
    """
    message_received = Signal(dict)
    state_changed = Signal(str)

    def __init__(self, base_ws: str = "ws://127.0.0.1/ws/chat", *, token: str = ""):
        super().__init__()
        self.base_ws = base_ws.rstrip("/")
        self.token = token
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._ws = None
        self._room_id: Optional[str] = None
        self._stop = threading.Event()

    def connect_room(self, room_id: str | int):
        """Переподключение к новой комнате: закрываем прежнее, открываем новое соединение."""
        self._room_id = str(room_id)
        self.stop()
        self._stop.clear()
        def runner():
            asyncio.run(self._run())
        self._thread = threading.Thread(target=runner, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._loop:
            def _cancel():
                for task in asyncio.all_tasks(self._loop):
                    task.cancel()
            try:
                self._loop.call_soon_threadsafe(_cancel)
            except Exception:
                pass

    async def _run(self):
        if not self._room_id:
            return
        self._loop = asyncio.get_running_loop()
        url = f"{self.base_ws}/{self._room_id}/?token={self.token}"
        backoff = 1.0
        while not self._stop.is_set():
            try:
                async with websockets.connect(
                    url,
                    ping_interval=30,
                    ping_timeout=20,
                    max_queue=64
                ) as ws:
                    self._ws = ws
                    self.state_changed.emit("connected")
                    # receiver loop
                    while not self._stop.is_set():
                        raw = await ws.recv()
                        try:
                            evt = json.loads(raw)
                        except Exception:
                            continue
                        self.message_received.emit(evt)
            except asyncio.CancelledError:
                break
            except Exception:
                self.state_changed.emit("disconnected")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 10)
            else:
                backoff = 1.0
            finally:
                self.state_changed.emit("disconnected")
                self._ws = None

    async def _send_json(self, data: dict):
        if self._ws:
            try:
                await self._ws.send(json.dumps(data, ensure_ascii=False))
            except Exception:
                pass

    def send_text(self, content: str, message_type: str = "text"):
        """
        Опционально: отправка через WS (создаст сообщение от имени JWT-пользователя).
        В нашем клиенте основная отправка идёт через HTTP, так что метод можно не использовать.
        """
        if not self._loop:
            return
        payload = {"type": "send_message", "content": content, "message_type": message_type}
        try:
            self._loop.call_soon_threadsafe(lambda: asyncio.create_task(self._send_json(payload)))
        except Exception:
            pass
