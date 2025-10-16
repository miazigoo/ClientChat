import os
import threading
from PySide6.QtCore import QDateTime, QMetaObject, Qt, Slot, QTimer
from realtime.realtime_client import FakeRealtimeClient
from data.sqlite_store import repo

try:
    from realtime.client import ChatClient

    HAS_WS = True
except Exception:
    HAS_WS = False


class RealtimeHandler:
    """Обработчик real-time соединений с автопереподключением"""

    def __init__(self, main_window):
        self.main_window = main_window
        self._connection_check_timer = QTimer()
        self._connection_check_timer.setInterval(10000)  # проверяем каждые 10 секунд
        self._connection_check_timer.timeout.connect(self._check_connection_status)

    def init_realtime(self):
        """Инициализация real-time соединений"""
        mw = self.main_window

        # Начальное состояние
        self._update_connection_status("disconnected", "Подключение...")

        print(f"DEBUG: HAS_WS = {HAS_WS}")
        print(f"DEBUG: WS_AUTH_USER = {os.getenv('WS_AUTH_USER')}")
        print(f"DEBUG: fx_id = {mw.user_data.get('id')}")
        print(f"DEBUG: operator_id = {mw.user_data.get('operator_id')}")

        # Авторизация для WS
        ws_user = os.getenv("WS_AUTH_USER")
        ws_pass = os.getenv("WS_AUTH_PASSWORD")

        if ws_user and ws_pass:
            code, payload = mw.backend_api.login(ws_user, ws_pass)
            print(f"DEBUG: login result = {code}, {payload}")
            if code and 200 <= code < 300:
                mw.jwt_token = payload.get("access")
                print(f"DEBUG: Got JWT token: {mw.jwt_token[:20]}..." if mw.jwt_token else "No token")

        # Если кредов оператора нет — логинимся как клиент
        if not mw.jwt_token and mw.user_data.get("id") and mw.user_data.get("operator_id"):
            print("DEBUG: Trying fx_login...")
            code, payload = mw.backend_api.fx_login(mw.user_data["id"], mw.user_data["operator_id"])
            print(f"DEBUG: fx_login result = {code}, {payload}")
            if code and 200 <= code < 300:
                mw.jwt_token = payload.get("access")
                mw.ws_username = payload.get("username")
                inst = payload.get("instance_uid")
                if inst:
                    mw.agent_ids.instance_id = inst

        ws_base = os.getenv("DJANGO_WS_BASE", "ws://89.104.67.225:80/ws/chat")
        print(f"DEBUG: ws_base = {ws_base}")
        print(f"DEBUG: final jwt_token = {'Present' if mw.jwt_token else 'None'}")

        if HAS_WS and mw.jwt_token:
            # Настоящий ChatClient
            mw.ws = ChatClient(base_ws=ws_base, token=mw.jwt_token)
            mw.ws.state_changed.connect(self._on_ws_state_changed)
            mw.ws.message_received.connect(self._on_django_ws_event)
            mw.ws.connection_error.connect(self._on_connection_error)
            self._connection_check_timer.start()
        else:
            if os.getenv("USE_FAKE_RT", "0") == "1":
                # Заглушка
                mw.rtc = FakeRealtimeClient(mw.user_data["id"])
                mw.rtc.connected.connect(lambda: self._update_connection_status("connected", "Подключен"))
                mw.rtc.disconnected.connect(lambda: self._update_connection_status("disconnected", "Отключен"))
                mw.rtc.connection_error.connect(self._on_connection_error)
                mw.rtc.message_received.connect(self._on_rt_message)
                mw.rtc.status_changed.connect(self._on_rt_status)
                mw.rtc.connect()
                self._connection_check_timer.start()
            else:
                self._update_connection_status("no_service", "Служба недоступна")

    def _on_ws_state_changed(self, state: str):
        """Обработка изменения состояния WS"""
        status_map = {
            "connected": ("connected", "Подключен"),
            "disconnected": ("disconnected", "Отключен"),
            "connecting": ("connecting", "Подключение..."),
            "reconnecting": ("reconnecting", "Переподключение...")
        }

        status, text = status_map.get(state, ("unknown", "Неизвестное состояние"))
        self._update_connection_status(status, text)

    def _on_connection_error(self, error_message: str):
        """Обработка ошибок подключения"""
        mw = self.main_window
        print(f"Connection error: {error_message}")
        mw.status_bar.showMessage(f"Ошибка соединения: {error_message}", 8000)

    def _update_connection_status(self, status: str, text: str):
        """Обновление статуса подключения в UI"""
        mw = self.main_window

        emoji_map = {
            "connected": "🟢",
            "disconnected": "🔴",
            "connecting": "🟡",
            "reconnecting": "🟠",
            "no_service": "⚫"
        }

        emoji = emoji_map.get(status, "⚪")
        mw.connection_status.setText(f"{emoji} {text}")

    def _check_connection_status(self):
        """Периодическая проверка состояния соединения"""
        mw = self.main_window

        # Проверяем состояние основного соединения
        if hasattr(mw, "ws") and mw.ws:
            current_state = mw.ws.get_connection_state()
            if current_state == "disconnected":
                # Пытаемся переподключиться если есть активный чат
                if mw.active_chat:
                    room_id = mw.backend_rooms.get(mw.active_chat["id"])
                    if room_id:
                        self.subscribe_ws(mw.active_chat["id"])

        elif hasattr(mw, "rtc") and mw.rtc:
            if not mw.rtc.is_connected():
                self._update_connection_status("reconnecting", "Переподключение...")
                mw.rtc.connect()

    def ws_start_chat(self, chat_id: str):
        """Запуск WS для чата"""
        self._subscribe_ws(chat_id)

    def subscribe_ws(self, chat_id: str):
        """Подписка на WS комнату для чата"""
        mw = self.main_window

        print(f"DEBUG: subscribe_ws called for chat_id={chat_id}")
        print(f"DEBUG: backend_rooms = {mw.backend_rooms}")
        print(f"DEBUG: has ws = {hasattr(mw, 'ws') and mw.ws}")
        print(f"DEBUG: jwt_token present = {'Yes' if mw.jwt_token else 'No'}")

        room_id = mw.backend_rooms.get(chat_id)
        print(f"DEBUG: room_id for chat {chat_id} = {room_id}")

        if room_id and hasattr(mw, "ws") and mw.ws and mw.jwt_token:
            print(f"DEBUG: All conditions met, trying to connect to room {room_id}")

            # Проверяем текущее состояние перед подключением
            current_state = mw.ws.get_connection_state()
            print(f"DEBUG: Current WS state: {current_state}")

            if current_state in ["disconnected", "reconnecting"]:
                self._update_connection_status("connecting", "Подключение к чату...")

            try:
                print(f"DEBUG: Calling connect_room({room_id})")
                mw.ws.connect_room(str(room_id))
                print("DEBUG: connect_room called successfully")
                mw.left_chat = False
                # Разблокируем ввод при подключении к новой комнате
                mw.message_input.setDisabled(False)
                mw.send_btn.setDisabled(False)
                mw.attach_btn.setDisabled(False)
                mw.apply_theme()
            except Exception as e:
                print(f"DEBUG: connect_room failed: {e}")
        elif not room_id:
            print("DEBUG: No room_id found - setting status to no_room")
            self._update_connection_status("no_room", "Комната не найдена")
        else:
            print("DEBUG: Some condition failed:")
            print(f"  room_id: {room_id}")
            print(f"  has ws: {hasattr(mw, 'ws') and mw.ws}")
            print(f"  jwt_token: {'Yes' if mw.jwt_token else 'No'}")

    def rt_send(self, text: str):
        """Отправка через real-time соединение"""
        mw = self.main_window

        if mw.active_chat is None:
            return

        # Проверяем состояние соединения перед отправкой
        if hasattr(mw, "ws") and mw.ws:
            if mw.ws.get_connection_state() != "connected":
                mw.status_bar.showMessage("Нет подключения для отправки сообщения", 5000)
                return
        elif hasattr(mw, "rtc") and mw.rtc:
            if not mw.rtc.is_connected():
                mw.status_bar.showMessage("Нет подключения для отправки сообщения", 5000)
                return
            mw.rtc.send_message(mw.active_chat["id"], text)

    # Остальные методы остаются без изменений...
    def _subscribe_ws(self, chat_id: str):
        """Внутренний метод подписки на WS"""
        return self.subscribe_ws(chat_id)

    def _on_rt_message(self, chat_id, msg):
        """Обработка сообщения от заглушки RT клиента"""
        mw = self.main_window

        msg.setdefault("time", QDateTime.currentDateTime().toString("hh:mm"))
        chat = mw.chats_by_id.get(chat_id)
        if not chat:
            return

        chat["messages"].append(msg)
        repo.add_message(chat_id, sender=msg.get("sender", "operator"), text=msg.get("text"),
                         operator=msg.get("operator"), time_str=msg.get("time"))

        if chat.get("status") != "В работе":
            chat["status"] = "В работе"
            repo.update_chat_status(chat_id, "В работе")

        chat["updated_at"] = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm")
        mw.chat_list.upsert_chat(chat)

        if mw.active_chat and mw.active_chat["id"] == chat_id:
            mw.chat_area.add_message(msg["text"], is_user=(msg.get("sender") == "user"), operator=msg.get("operator"))
            mw.update_header_for_chat()

    def _on_rt_status(self, chat_id, status):
        """Обработка изменения статуса от заглушки RT клиента"""
        mw = self.main_window
        mw.chat_manager.change_status(chat_id, status)

    def _on_django_ws_event(self, evt: dict):
        """Обработка Django WS событий"""
        mw = self.main_window

        et = evt.get("type")

        if et == "new_message":
            m = evt.get("message") or {}
            # Эхо-фильтр: пропускаем свои же сообщения от клиента
            if (m.get("senderRole") == "client") or (mw.ws_username and m.get("senderName") == mw.ws_username):
                return

            room_id = str(m.get("roomId") or "")
            local_id = mw.room_to_local.get(room_id)
            if not local_id:
                return

            msg_id = str(m.get("id") or "")
            # отфильтруем эхо наших отправок через HTTP
            if msg_id and msg_id in mw._own_sent_ids:
                mw._own_sent_ids.discard(msg_id)
                return

            sender_name = m.get("senderName") or "Оператор"
            text = m.get("content") or ""
            time_str = QDateTime.currentDateTime().toString("hh:mm")

            chat = mw.chats_by_id.get(local_id)
            if not chat:
                return

            chat["messages"].append({"sender": "operator", "operator": sender_name, "text": text, "time": time_str})
            repo.add_message(local_id, sender="operator", text=text, operator=sender_name, time_str=time_str)

            if chat.get("status") != "В работе":
                chat["status"] = "В работе"
                repo.update_chat_status(local_id, "В работе")

            chat["updated_at"] = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm")
            mw.chat_list.upsert_chat(chat)

            if mw.active_chat and mw.active_chat["id"] == local_id:
                mw.chat_area.add_message(text, is_user=False, operator=sender_name)
                mw.update_header_for_chat()

        elif et == "room_update":
            room = evt.get("room") or {}
            room_id = str(room.get("id") or "")
            local_id = mw.room_to_local.get(room_id)
            if not local_id:
                return

            ops = room.get("operatorsCount")
            parts = room.get("participantsCount")
            chat = mw.chats_by_id.get(local_id)
            if chat is None:
                return

            if ops is not None:
                chat["operators_count"] = int(ops)
            if parts is not None:
                chat["participants_count"] = int(parts)

            if mw.active_chat and mw.active_chat["id"] == local_id:
                count_text = f"Операторов: {chat.get('operators_count', 0)}"
                mw.operator_count_label.setText(count_text)

    def send_text_with_retry(self, chat_id: str, text: str, attempt: int = 0, max_attempts: int = 40,
                             delay_ms: int = 100):
        """Отправка текста с повторами"""
        mw = self.main_window

        if attempt >= max_attempts:
            mw.status_bar.showMessage("Превышено максимальное количество попыток отправки", 5000)
            return

        room_id = mw.backend_rooms.get(chat_id)
        if not room_id:
            retry_timer = QTimer()
            retry_timer.setSingleShot(True)
            retry_timer.timeout.connect(
                lambda: self.send_text_with_retry(chat_id, text, attempt + 1, max_attempts, delay_ms)
            )
            retry_timer.start(delay_ms)
            return

        def _send_msg():
            try:
                code, resp = mw.backend_api.send_message(room_id, mw.agent_ids.instance_id, message=text)
                if not (code and 200 <= code < 300):
                    print("Backend send_message error:", resp)
                    QMetaObject.invokeMethod(mw, "_on_send_error", Qt.QueuedConnection)
                else:
                    msg_id = str((resp or {}).get("id") or "")
                    if msg_id:
                        mw._own_sent_ids.add(msg_id)
            except Exception as e:
                print(f"Exception during send: {e}")
                QMetaObject.invokeMethod(mw, "_on_send_error", Qt.QueuedConnection)

        threading.Thread(target=_send_msg, daemon=True).start()

    def send_files_with_retry(self, chat_id: str, paths: list[str], attempt: int = 0, max_attempts: int = 40,
                              delay_ms: int = 100):
        """Отправка файлов с повторами"""
        mw = self.main_window

        room_id = mw.backend_rooms.get(chat_id)
        if not room_id:
            if attempt < max_attempts:
                QTimer.singleShot(delay_ms,
                                  lambda: self.send_files_with_retry(chat_id, paths, attempt + 1, max_attempts,
                                                                     delay_ms))
            else:
                mw.status_bar.showMessage("Комната на сервере не готова. Повторите попытку.", 5000)
            return

        def _send_files():
            code, resp = mw.backend_api.send_files(room_id, mw.agent_ids.instance_id, files=paths)
            if not (code and 200 <= code < 300):
                print("Backend send_files error:", resp)
                mw.status_bar.showMessage("Ошибка загрузки файлов на сервер", 5000)

        threading.Thread(target=_send_files, daemon=True).start()

    def leave_chat(self):
        """Покинуть активный чат"""
        mw = self.main_window

        if not mw.active_chat:
            return

        room_id = mw.backend_rooms.get(mw.active_chat["id"])
        if not room_id:
            mw.status_bar.showMessage("Комната ещё не создана на сервере", 4000)
            return

        def _leave():
            code, resp = mw.backend_api.client_leave(room_id, mw.agent_ids.instance_id)
            if code and 200 <= code < 300:
                QMetaObject.invokeMethod(mw, "_on_leave_success_ui", Qt.QueuedConnection)
            else:
                QMetaObject.invokeMethod(mw, "_on_leave_error_ui", Qt.QueuedConnection)

        threading.Thread(target=_leave, daemon=True).start()

    def on_leave_success_ui(self):
        """Успешное покидание чата - UI обработка"""
        mw = self.main_window
        mw.left_chat = True
        mw.message_input.setDisabled(True)
        mw.send_btn.setDisabled(True)
        mw.attach_btn.setDisabled(True)
        mw.status_bar.showMessage("Вы покинули чат", 5000)
        mw.update_header_for_chat()
        mw.apply_theme()

    def on_leave_error_ui(self):
        """Ошибка покидания чата - UI обработка"""
        mw = self.main_window
        mw.status_bar.showMessage("Не удалось покинуть чат", 5000)

    def on_send_error(self):
        """Обработка ошибки отправки сообщения"""
        mw = self.main_window
        mw.status_bar.showMessage("Ошибка отправки на сервер", 5000)

    def close_connections(self):
        """Закрытие всех соединений при завершении работы"""
        mw = self.main_window

        try:
            self._connection_check_timer.stop()
            if hasattr(mw, "ws") and mw.ws:
                mw.ws.stop()
            elif hasattr(mw, "rtc"):
                mw.rtc.disconnect()
        except Exception:
            pass

    def leave_chat_for(self, chat_id: str, *, update_ui: bool = False):
        """Покинуть указанный чат (может быть неактивным).
           update_ui=True — обновить UI, только если этот чат активен.
        """
        mw = self.main_window

        room_id = mw.backend_rooms.get(chat_id)
        if not room_id:
            # Комната ещё не создана на сервере — просто выходим
            return

        def _leave():
            code, resp = mw.backend_api.client_leave(room_id, mw.agent_ids.instance_id)
            if not (code and 200 <= code < 300):
                # игнорируем ошибку на массовых операциях удаления
                return

            if update_ui and mw.active_chat and mw.active_chat["id"] == chat_id:
                from PySide6.QtCore import QMetaObject, Qt
                QMetaObject.invokeMethod(mw, "_on_leave_success_ui", Qt.QueuedConnection)

        threading.Thread(target=_leave, daemon=True).start()
