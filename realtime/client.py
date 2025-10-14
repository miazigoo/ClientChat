import asyncio
import json
import threading
from typing import Optional
from PySide6.QtCore import QObject, Signal
import websockets


class ChatClient(QObject):
    """
    Channels-совместимый WS-клиент с улучшенным переподключением
    """
    message_received = Signal(dict)
    state_changed = Signal(str)
    connection_error = Signal(str)

    def __init__(self, base_ws: str = "ws://127.0.0.1/ws/chat", *, token: str = ""):
        super().__init__()
        self.base_ws = base_ws.rstrip("/")
        self.token = token
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._ws = None
        self._room_id: Optional[str] = None
        self._stop = threading.Event()
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 10

    def connect_room(self, room_id: str | int):
        """Переподключение к новой комнате"""
        self._room_id = str(room_id)
        self._reconnect_attempts = 0
        self.stop()
        self._stop.clear()

        def runner():
            asyncio.run(self._run())

        self._thread = threading.Thread(target=runner, daemon=True)
        self._thread.start()

    def stop(self):
        """Остановка клиента"""
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
        """Основной цикл с переподключением"""
        if not self._room_id:
            self.connection_error.emit("Не указан ID комнаты")
            return

        self._loop = asyncio.get_running_loop()
        url = f"{self.base_ws}/{self._room_id}/?token={self.token}"

        print(f"DEBUG ChatClient: Attempting to connect to: {url}")
        print(f"DEBUG ChatClient: Token: {self.token[:50]}..." if self.token else "No token")

        while not self._stop.is_set() and self._reconnect_attempts < self._max_reconnect_attempts:
            try:
                self.state_changed.emit("connecting")
                print(f"DEBUG ChatClient: Connecting, attempt {self._reconnect_attempts + 1}")

                async with websockets.connect(
                        url,
                        ping_interval=30,
                        ping_timeout=20,
                        max_queue=64,
                        open_timeout=10,
                        close_timeout=10
                ) as ws:
                    print("DEBUG ChatClient: WebSocket connection successful!")
                    self._ws = ws
                    self._reconnect_attempts = 0  # сбрасываем счетчик при успешном подключении
                    self.state_changed.emit("connected")

                    # Основной цикл получения сообщений
                    while not self._stop.is_set():
                        try:
                            raw = await asyncio.wait_for(ws.recv(), timeout=60.0)
                            print(f"DEBUG ChatClient: Received message: {raw}")
                            try:
                                evt = json.loads(raw)
                                self.message_received.emit(evt)
                            except json.JSONDecodeError as e:
                                self.connection_error.emit(f"Ошибка парсинга сообщения: {e}")
                        except asyncio.TimeoutError:
                            # Отправляем ping для проверки соединения
                            try:
                                await ws.ping()
                            except Exception:
                                break
                        except websockets.exceptions.ConnectionClosed:
                            print("DEBUG ChatClient: Connection closed by server")
                            break

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._reconnect_attempts += 1
                self.state_changed.emit("disconnected")

                error_msg = f"Ошибка подключения (попытка {self._reconnect_attempts}/{self._max_reconnect_attempts}): {str(e)}"
                print(f"DEBUG ChatClient: {error_msg}")
                self.connection_error.emit(error_msg)

                if self._reconnect_attempts < self._max_reconnect_attempts:
                    # Экспоненциальная задержка: 1, 2, 4, 8, 16, ... секунд (макс 30)
                    backoff = min(2 ** self._reconnect_attempts, 30)
                    self.state_changed.emit("reconnecting")
                    print(f"DEBUG ChatClient: Waiting {backoff}s before reconnect...")
                    await asyncio.sleep(backoff)
                else:
                    self.connection_error.emit("Достигнуто максимальное количество попыток переподключения")
                    break
            finally:
                if not self._stop.is_set():
                    self.state_changed.emit("disconnected")
                self._ws = None

    async def _send_json(self, data: dict):
        """Отправка JSON данных"""
        if self._ws and not self._ws.closed:
            try:
                await self._ws.send(json.dumps(data, ensure_ascii=False))
                return True
            except Exception as e:
                self.connection_error.emit(f"Ошибка отправки сообщения: {e}")
                return False
        return False

    def send_text(self, content: str, message_type: str = "text"):
        """Отправка текстового сообщения через WS"""
        if not self._loop:
            self.connection_error.emit("Нет активного соединения")
            return

        payload = {"type": "send_message", "content": content, "message_type": message_type}
        try:
            self._loop.call_soon_threadsafe(lambda: asyncio.create_task(self._send_json(payload)))
        except Exception as e:
            self.connection_error.emit(f"Ошибка планирования отправки: {e}")

    def get_connection_state(self):
        """Получение текущего состояния подключения"""
        try:
            if self._ws:
                # Проверяем разные возможные атрибуты состояния
                if hasattr(self._ws, 'closed'):
                    return "connected" if not self._ws.closed else "disconnected"
                elif hasattr(self._ws, 'close_code'):
                    return "connected" if self._ws.close_code is None else "disconnected"
                else:
                    # Если нет явного атрибута состояния, считаем подключенным
                    return "connected"
        except Exception as e:
            print(f"DEBUG: Error checking WS state: {e}")
            return "disconnected"

        if self._reconnect_attempts > 0:
            return "reconnecting"
        else:
            return "disconnected"
