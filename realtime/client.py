import asyncio
import json
import threading
import uuid
from typing import Optional
from PySide6.QtCore import QObject, Signal
import websockets

class ChatClient(QObject):
    message_received = Signal(dict)
    state_changed = Signal(str)

    def __init__(self, uri: str = "ws://127.0.0.1:8765", *, agent_instance_id: str = None, agent_operator_id: str = None):
        super().__init__()
        self.uri = uri
        self.client_id = uuid.uuid4().hex
        self._thread = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._ws = None
        self._outgoing: Optional[asyncio.Queue] = None
        self._room: Optional[str] = None
        self._stop = threading.Event()
        self.agent_instance_id = agent_instance_id
        self.agent_operator_id = agent_operator_id

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
        backoff = 1.0
        while not self._stop.is_set():
            try:
                async with websockets.connect(self.uri) as ws:
                    self._ws = ws
                    self.state_changed.emit("connected")

                    # HELLO от агента
                    await self._send({
                        "type": "hello",
                        "client_id": self.client_id,
                        "agent": {"instance_id": self.agent_instance_id, "operator_id": self.agent_operator_id}
                    })
                    # Подписка, если была установлена до подключения
                    if self._room:
                        await self._send({"type": "subscribe", "room": self._room})

                    sender = asyncio.create_task(self._sender())
                    receiver = asyncio.create_task(self._receiver())

                    done, pending = await asyncio.wait(
                        {sender, receiver},
                        return_when=asyncio.FIRST_EXCEPTION
                    )
                    for t in pending:
                        t.cancel()
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

    def subscribe(self, room: str):
        self._room = room
        if self._outgoing and self._loop:
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
        if self._outgoing and self._loop:
            self._loop.call_soon_threadsafe(lambda: self._outgoing.put_nowait(payload))

    def start_chat(self, dialog_id: str, user_id: str):
        room = f"dialog:{dialog_id}"
        self.subscribe(room)
        payload = {
            "type": "start_chat",
            "room": room,
            "dialog_id": dialog_id,
            "user_id": user_id,
            "agent": {"instance_id": self.agent_instance_id, "operator_id": self.agent_operator_id},
        }
        if self._outgoing and self._loop:
            self._loop.call_soon_threadsafe(lambda: self._outgoing.put_nowait(payload))