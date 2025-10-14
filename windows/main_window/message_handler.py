import os
from PySide6.QtCore import QDateTime, Qt
from PySide6.QtWidgets import QFileDialog, QTextEdit, QMessageBox
from data.sqlite_store import repo
from styles.theme_manager import theme_manager


class MessageHandler:
    """Обработчик сообщений и файлов"""

    def __init__(self, main_window):
        self.main_window = main_window

    def send_message(self):
        """Отправка сообщения"""
        mw = self.main_window

        text = mw.message_input.toPlainText().strip()
        if not text:
            return

        if not mw.active_chat:
            mw.chat_manager.show_empty_state()
            return

        # Добавляем сообщение в UI
        mw.chat_area.add_message(text, is_user=True)
        mw.message_input.clear()

        # Сохраняем в базу данных
        msg_time = QDateTime.currentDateTime().toString("hh:mm")
        mw.active_chat["messages"].append({"sender": "user", "text": text, "time": msg_time})

        # Обновляем статус
        mw.active_chat["status"] = "Ожидает оператора"
        mw.active_chat["updated_at"] = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm")

        repo.add_message(mw.active_chat["id"], sender="user", text=text, time_str=msg_time)
        repo.update_chat_status(mw.active_chat["id"], "Ожидает оператора")

        mw.theme_handler.update_header_for_chat()
        mw.chat_list.upsert_chat(mw.active_chat)

        # Отправка через WS или заглушку
        mw.realtime_handler.rt_send(text)

        # Отправка на сервер
        mw.realtime_handler.send_text_with_retry(mw.active_chat["id"], text)

        # Обновляем статус
        timestamp = QDateTime.currentDateTime().toString('hh:mm:ss')
        mw.status_bar.showMessage(f"Сообщение отправлено в {timestamp}")

    def attach_file(self):
        """Прикрепление файла"""
        mw = self.main_window

        file_path, _ = QFileDialog.getOpenFileName(
            mw,
            "Выберите файл",
            "",
            "Все файлы (*.*)"
        )

        if file_path:
            self.on_files_dropped([file_path])

    def on_files_dropped(self, paths):
        """Обработка drag&drop файлов"""
        mw = self.main_window

        if not mw.active_chat:
            # если нет активного чата — создаем новый автоматически
            mw.chat_manager.create_new_chat()

        for p in paths:
            attach = self._build_attachment_data(p)
            mw.chat_area.add_attachment(attach, is_user=True)

            msg_time = QDateTime.currentDateTime().toString("hh:mm")
            mw.active_chat["messages"].append({"sender": "user", "attachment": attach, "time": msg_time})
            repo.add_message(mw.active_chat["id"], sender="user", attachment=attach, time_str=msg_time)

        # Обновляем статус
        mw.active_chat["status"] = "Ожидает оператора"
        mw.active_chat["updated_at"] = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm")
        mw.theme_handler.update_header_for_chat()
        mw.chat_list.upsert_chat(mw.active_chat)

        mw.realtime_handler.rt_send("[attachment]")
        mw.realtime_handler.send_files_with_retry(mw.active_chat["id"], list(paths))

    def handle_key_press(self, event):
        """Обработка клавиш в поле ввода"""
        mw = self.main_window

        if event.key() == Qt.Key_Return and not event.modifiers() == Qt.ShiftModifier:
            self.send_message()
            event.accept()
        else:
            QTextEdit.keyPressEvent(mw.message_input, event)

    def logout(self):
        """Выход из системы"""
        mw = self.main_window

        reply = QMessageBox.question(
            mw,
            'Подтверждение выхода',
            'Вы действительно хотите выйти из системы?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            mw.close()

    def _build_attachment_data(self, path: str):
        """Построение данных о прикрепленном файле"""
        name = os.path.basename(path)

        try:
            size = self._human_size(os.path.getsize(path))
        except Exception:
            size = ""

        ext = os.path.splitext(name)[1].lower()
        is_image = ext in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}

        return {
            "path": path,
            "name": name,
            "size": size,
            "is_image": is_image
        }

    def _human_size(self, num):
        """Конвертация размера файла в человекочитаемый формат"""
        for unit in ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ']:
            if abs(num) < 1024.0:
                return f"{num:.1f} {unit}"
            num /= 1024.0
        return f"{num:.1f} ПБ"

    def setup_message_input_handler(self):
        """Настройка обработчика ввода сообщений"""
        mw = self.main_window

        # Переопределяем keyPressEvent для поля ввода
        mw.message_input.keyPressEvent = self.handle_key_press

    def connect_message_signals(self):
        """Подключение сигналов для работы с сообщениями"""
        mw = self.main_window

        # Подключаем сигналы кнопок
        mw.send_btn.clicked.connect(self.send_message)
        mw.attach_btn.clicked.connect(self.attach_file)

        # Подключаем drag&drop
        if hasattr(mw, 'chat_area'):
            mw.chat_area.files_dropped.connect(self.on_files_dropped)

        # Подключаем кнопку создания из empty state
        if hasattr(mw, 'empty_create_btn'):
            mw.empty_create_btn.clicked.connect(mw.chat_manager.create_new_chat)

        # Подключаем кнопки боковой панели
        mw.new_chat_btn.clicked.connect(mw.chat_manager.create_new_chat)
        mw.history_btn.clicked.connect(mw.chat_manager.open_history)
        mw.settings_btn.clicked.connect(mw.chat_manager.open_settings)
        mw.logout_btn.clicked.connect(self.logout)
        mw.leave_chat_btn.clicked.connect(mw.realtime_handler.leave_chat)

        # Подключаем toolbar actions
        if hasattr(mw, 'toolbar_actions'):
            mw.toolbar_actions['new_chat'].triggered.connect(mw.chat_manager.create_new_chat)
            mw.toolbar_actions['rename'].triggered.connect(lambda: mw.chat_manager.rename_chat())
            mw.toolbar_actions['settings'].triggered.connect(mw.chat_manager.open_settings)
            mw.toolbar_actions['theme_toggle'].triggered.connect(theme_manager.toggle_theme)

        # Подключаем left panel signals
        mw.search_input.textChanged.connect(mw.chat_manager.apply_chat_filters)
        mw.status_filter.currentIndexChanged.connect(mw.chat_manager.apply_chat_filters)
        mw.bulk_close_btn.clicked.connect(mw.chat_manager.bulk_close_selected)
        mw.bulk_delete_btn.clicked.connect(mw.chat_manager.bulk_delete_selected)

        # Подключаем chat list signals
        mw.chat_list.chat_selected.connect(mw.chat_manager.set_active_chat)
        mw.chat_list.chat_rename.connect(mw.chat_manager.rename_chat)
        mw.chat_list.chat_delete.connect(mw.chat_manager.delete_chat)
        mw.chat_list.chat_change_status.connect(mw.chat_manager.change_status)

    def validate_message_input(self, text: str) -> bool:
        """Валидация введенного сообщения"""
        if not text or not text.strip():
            return False

        # Проверка максимальной длины
        max_length = 5000  # например
        if len(text) > max_length:
            QMessageBox.warning(
                self.main_window,
                "Слишком длинное сообщение",
                f"Максимальная длина сообщения: {max_length} символов"
            )
            return False

        return True

    def get_allowed_file_extensions(self):
        """Получение списка разрешенных расширений файлов"""
        return {
            'images': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'],
            'documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
            'archives': ['.zip', '.rar', '.7z'],
            'other': ['.csv', '.xlsx', '.ppt', '.pptx']
        }

    def validate_file(self, file_path: str) -> tuple[bool, str]:
        """Валидация загружаемого файла"""
        if not os.path.exists(file_path):
            return False, "Файл не найден"

        # Проверка размера файла (например, максимум 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        try:
            file_size = os.path.getsize(file_path)
            if file_size > max_size:
                return False, f"Файл слишком большой. Максимальный размер: {self._human_size(max_size)}"
        except Exception:
            return False, "Не удалось определить размер файла"

        return True, "OK"
