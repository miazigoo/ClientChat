from PySide6.QtCore import QDateTime, QTimer
from PySide6.QtWidgets import QInputDialog, QMessageBox
from data.sqlite_store import repo
import threading
from windows.widgets.history_dialog import HistoryDialog
from windows.settings_dialog import SettingsDialog


class ChatManager:
    """Менеджер работы с чатами"""

    def __init__(self, main_window):
        self.main_window = main_window

    def load_user_chats(self):
        """Загружаем чаты конкретного пользователя из базы данных"""
        mw = self.main_window
        user_id = mw.user_data["id"]
        mw.chats = repo.load_user_chats(user_id)
        mw.chats_by_id = {c["id"]: c for c in mw.chats}

    def build_left_list(self):
        """Построение списка чатов в левой панели"""
        mw = self.main_window
        mw.chat_list.set_chats(mw.chats)

    def apply_chat_filters(self):
        """Применение фильтров к списку чатов"""
        mw = self.main_window
        query = (mw.search_input.text() or "").strip().lower()
        status = mw.status_filter.currentText()
        filtered = []

        for c in mw.chats:
            # Фильтр по статусу
            if status != "Все статусы" and c.get("status") != status:
                continue
            # Фильтр по поисковому запросу
            if query and (query not in c["title"].lower() and query not in c["id"].lower()):
                continue
            filtered.append(c)

        mw.chat_list.set_chats(filtered)
        # подсветим активный, если он в фильтре
        if mw.active_chat and any(c["id"] == mw.active_chat["id"] for c in filtered):
            mw.chat_list.select_chat(mw.active_chat["id"])

    def select_initial_chat(self):
        """Выбираем начальный чат: сначала 'В работе', затем 'Новая', иначе первый или создаем новый"""
        mw = self.main_window
        chat = None

        # Приоритет статусов для автовыбора
        for st in ("В работе", "Новая"):
            for c in mw.chats:
                if c["status"] == st:
                    chat = c
                    break
            if chat:
                break

        if not chat and mw.chats:
            chat = mw.chats[0]

        if not chat:
            chat = self._create_chat_object(title="Общая заявка", status="Новая")
            self._add_chat(chat)

        self.set_active_chat(chat["id"])

    def set_active_chat(self, chat_id):
        """Установка активного чата"""
        mw = self.main_window

        chat = repo.get_chat(chat_id)
        if not chat:
            return

        mw.chats_by_id[chat_id] = chat
        mw.active_chat = chat
        mw.update_header_for_chat()

        # Безопасная загрузка сообщений
        try:
            mw.chat_area.load_messages(mw.active_chat.get("messages", []))
        except Exception as e:
            print(f"Error loading messages: {e}")
            mw.chat_area.clear_messages()

        mw.center_stack.setCurrentIndex(mw.CENTER_CHAT)
        mw.chat_list.select_chat(chat_id)

        # WS подключение только если есть room_id
        if chat_id in mw.backend_rooms:
            mw.realtime_handler.subscribe_ws(chat_id)

    def show_empty_state(self):
        """Показать пустое состояние (нет активного чата)"""
        mw = self.main_window
        mw.active_chat = None
        mw.center_stack.setCurrentIndex(mw.CENTER_EMPTY)
        mw.update_header_for_chat()

    def create_new_chat(self):
        """Создание нового чата"""
        mw = self.main_window

        title, ok = self._ask_new_chat_title()
        if not ok:
            return

        chat = repo.create_chat(mw.user_data["id"], title or "Новая заявка")
        self._add_chat(chat)
        mw.chat_list.upsert_chat(chat)
        self.set_active_chat(chat["id"])

        print(f"DEBUG: Created chat with ID: {chat['id']}")

        # Отправляем запрос на создание комнаты в бэкенде
        def _send_start_backend():
            print(f"DEBUG: Starting backend request for chat {chat['id']}")
            code, payload = mw.backend_api.start_chat(
                instance_uid=mw.agent_ids.instance_id,
                crm_client_fio=mw.agent_ids.operator_id,
                title=title or "Новая заявка",
                message=""
            )
            print(f"DEBUG: Backend response: {code}, {payload}")

            if code and 200 <= code < 300:
                room = (payload or {}).get("room") or {}
                room_id = room.get("id")
                print(f"DEBUG: Got room_id: {room_id}")

                if room_id:
                    # Используем QMetaObject для безопасного вызова из потока
                    from PySide6.QtCore import QMetaObject, Qt

                    print(f"DEBUG: About to call QMetaObject.invokeMethod")

                    # Определяем функцию в области видимости главного потока
                    def update_room_mapping():
                        try:
                            print(f"DEBUG: update_room_mapping called in UI thread")
                            print(f"DEBUG: chat['id'] = {chat['id']}")
                            print(f"DEBUG: room_id = {room_id}")
                            print(f"DEBUG: mw.active_chat = {mw.active_chat['id'] if mw.active_chat else 'None'}")

                            mw.backend_rooms[chat["id"]] = room_id
                            mw.room_to_local[str(room_id)] = chat["id"]
                            print(f"DEBUG: backend_rooms updated: {mw.backend_rooms}")

                            # подключаемся к WS комнате
                            if mw.active_chat and mw.active_chat["id"] == chat["id"]:
                                print(f"DEBUG: Active chat matches, calling subscribe_ws")
                                mw.realtime_handler.subscribe_ws(chat["id"])
                            else:
                                print(f"DEBUG: Active chat mismatch, will retry")

                                # Попытка через задержку
                                def retry_subscribe():
                                    if mw.active_chat and mw.active_chat["id"] == chat["id"]:
                                        print(f"DEBUG: Retry subscribe successful")
                                        mw.realtime_handler.subscribe_ws(chat["id"])
                                    else:
                                        print(f"DEBUG: Retry subscribe failed")

                                QTimer.singleShot(200, retry_subscribe)

                        except Exception as e:
                            print(f"Error in update_room_mapping: {e}")
                            import traceback
                            traceback.print_exc()

                    # Сохраняем функцию как метод экземпляра для QMetaObject
                    mw._temp_update_room_mapping = update_room_mapping
                    QMetaObject.invokeMethod(mw, "_temp_update_room_mapping", Qt.QueuedConnection)

                else:
                    print("DEBUG: No room_id in response")
            else:
                print(f"DEBUG: Backend request failed with code {code}")

        threading.Thread(target=_send_start_backend, daemon=True).start()
        mw.status_bar.showMessage(f"Создан новый чат {chat['id']}")

    def delete_chat(self, chat_id):
        """Удаление чата"""
        mw = self.main_window

        if chat_id not in mw.chats_by_id:
            return

        # сначала попросим сервер «покинуть чат» (если есть room_id)
        try:
            mw.realtime_handler.leave_chat_for(chat_id, update_ui=False)
        except Exception:
            pass  # не мешаем локальному удалению

        repo.delete_chat(chat_id)
        deleting_active = (mw.active_chat and mw.active_chat["id"] == chat_id)
        mw.chats = [c for c in mw.chats if c["id"] != chat_id]
        mw.chats_by_id.pop(chat_id, None)
        mw.chat_list.remove_chat(chat_id)

        if deleting_active:
            if mw.chats:
                self.set_active_chat(mw.chats[0]["id"])
            else:
                self.show_empty_state()

    def rename_chat(self, chat_id=None):
        """Переименование чата"""
        mw = self.main_window

        if chat_id is None:
            chat_id = mw.active_chat["id"] if mw.active_chat else None
        if not chat_id:
            return

        chat = mw.chats_by_id.get(chat_id)
        if not chat:
            return

        new_title, ok = QInputDialog.getText(
            mw, "Переименовать заявку", "Название:", text=chat["title"]
        )

        if ok and new_title.strip():
            chat["title"] = new_title.strip()
            chat["updated_at"] = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm")
            mw.chat_list.upsert_chat(chat)
            repo.rename_chat(chat_id, chat["title"])
            if mw.active_chat and mw.active_chat["id"] == chat_id:
                mw.update_header_for_chat()

    def change_status(self, chat_id, status):
        """Изменение статуса чата"""
        mw = self.main_window

        chat = mw.chats_by_id.get(chat_id)
        if not chat:
            return

        chat["status"] = status
        chat["updated_at"] = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm")
        mw.chat_list.upsert_chat(chat)

        if mw.active_chat and mw.active_chat["id"] == chat_id:
            mw.update_header_for_chat()
            repo.update_chat_status(chat_id, status)
            mw.apply_theme()

    def bulk_close_selected(self):
        """Массовое закрытие выбранных чатов"""
        mw = self.main_window

        ids = mw.chat_list.get_selected_ids()
        if not ids:
            return

        reply = QMessageBox.question(
            mw, "Закрыть заявки",
            f"Закрыть выбранные ({len(ids)}) заявки?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        for cid in ids:
            self.change_status(cid, "Закрыта")
        self.apply_chat_filters()

    def bulk_delete_selected(self):
        """Массовое удаление выбранных чатов"""
        mw = self.main_window

        ids = mw.chat_list.get_selected_ids()
        if not ids:
            return

        reply = QMessageBox.question(
            mw, "Удалить заявки",
            f"Удалить выбранные ({len(ids)}) заявки?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        for cid in ids:
            self.delete_chat(cid)
        self.apply_chat_filters()

    def open_history(self):
        """Открытие диалога истории чатов"""
        mw = self.main_window

        dlg = HistoryDialog(
            chats=mw.chats,
            on_open=self.set_active_chat,
            on_delete=self.delete_chat,
            parent=mw
        )
        dlg.exec()

    def open_settings(self):
        """Открытие диалога настроек"""
        mw = self.main_window
        dlg = SettingsDialog(mw)
        dlg.exec()

    def _ask_new_chat_title(self):
        """Запрос названия для нового чата"""
        mw = self.main_window
        return QInputDialog.getText(mw, "Новый чат", "Тема обращения:", text="Новая заявка")

    def _create_chat_object(self, title, status="Новая"):
        """Создание объекта чата"""
        mw = self.main_window

        new_id = self._next_chat_id()
        now_dt = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm")

        return {
            "id": new_id,
            "user_id": mw.user_data["id"],
            "title": title,
            "status": status,
            "created_at": now_dt,
            "updated_at": now_dt,
            "messages": [
                {
                    "sender": "operator",
                    "operator": "Головач Лена",
                    "text": "Здравствуйте! Чем можем помочь?",
                    "time": QDateTime.currentDateTime().toString("hh:mm")
                }
            ]
        }

    def _next_chat_id(self):
        """Генерация следующего ID чата"""
        mw = self.main_window

        existing = [c["id"] for c in mw.chats_by_id.values()]
        max_n = 0

        for cid in existing:
            try:
                n = int(cid.split("-")[1])
                max_n = max(max_n, n)
            except Exception:
                pass

        return f"CH-{max_n + 1:04d}"

    def _add_chat(self, chat):
        """Добавление чата в локальные структуры данных"""
        mw = self.main_window
        mw.chats.append(chat)
        mw.chats_by_id[chat["id"]] = chat
