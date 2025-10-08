# realtime/client.py
import asyncio
import json
import threading
import uuid
from typing import Optional
from PySide6.QtCore import QObject, Signal
import websockets

class ChatClient(QObject):
    message_received = Signal(dict)
    state_changed = Signal(str)  # "connected" | "disconnected"

    def __init__(self, uri: str = "ws://127.0.0.1:8765"):
        super().__init__()
        self.uri = uri
        self.client_id = uuid.uuid4().hex
        self._thread = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._ws = None
        self._outgoing: Optional[asyncio.Queue] = None
        self._room: Optional[str] = None
        self._stop = threading.Event()

    def start(self):
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
        self._loop = asyncio.get_running_loop()
        self._outgoing = asyncio.Queue()
        try:
            async with websockets.connect(self.uri) as ws:
                self._ws = ws
                self.state_changed.emit("connected")
                # Если уже устанавливали комнату до подключения — подпишемся
                if self._room:
                    await self._send({"type": "subscribe", "room": self._room})

                sender = asyncio.create_task(self._sender())
                receiver = asyncio.create_task(self._receiver())
                await asyncio.gather(sender, receiver)
        except asyncio.CancelledError:
            pass
        except Exception:
            self.state_changed.emit("disconnected")
        finally:
            self.state_changed.emit("disconnected")

    async def _send(self, data: dict):
        if not self._ws:
            return
        try:
            await self._ws.send(json.dumps(data, ensure_ascii=False))
        except Exception:
            pass

    async def _sender(self):
        while not self._stop.is_set():
            try:
                data = await self._outgoing.get()
            except asyncio.CancelledError:
                break
            await self._send(data)

    async def _receiver(self):
        while not self._stop.is_set():
            try:
                raw = await self._ws.recv()
            except asyncio.CancelledError:
                break
            except Exception:
                self.state_changed.emit("disconnected")
                break
            try:
                data = json.loads(raw)
            except Exception:
                continue
            self.message_received.emit(data)

    # Публичные методы для GUI-потока

    def subscribe(self, room: str):
        self._room = room
        if self._outgoing:
            self._loop.call_soon_threadsafe(lambda: self._outgoing.put_nowait({"type": "subscribe", "room": room}))

    def send_user_message(self, room: str, dialog_id: str, user_id: str, text: str):
        payload = {
            "type": "message",
            "room": room,
            "dialog_id": dialog_id,
            "sender": "user",
            "user_id": user_id,
            "client_id": self.client_id,
            "text": text,
        }
        if self._outgoing:
            self._loop.call_soon_threadsafe(lambda: self._outgoing.put_nowait(payload))
