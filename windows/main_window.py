import os
import mimetypes
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices, QImageReader
from windows.settings_dialog import SettingsDialog
from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QLabel, QPushButton, QTextEdit,
    QScrollArea, QFrame, QLineEdit, QSplitter,
    QListWidget, QListWidgetItem, QFileDialog,
    QMessageBox, QStatusBar, QToolBar, QDialog, QMenu,
    QStackedWidget, QInputDialog
)
from PySide6.QtCore import Qt, QTimer, QDateTime, Signal
from PySide6.QtGui import QFont, QIcon, QAction, QPixmap
import json
from styles.theme_manager import theme_manager, ThemeType
from data.test_data import TEST_CHATS  # тестовые чаты
from windows.widgets.chat_list import ChatList
from realtime.realtime_client import FakeRealtimeClient
from data.sqlite_store import repo
from agent.agent_ids import read_agent_ids
import threading
from integrations.backend_agent_api import BackendAgentAPI


# Попробуем использовать реальный WebSocket-клиент, при ошибке останется заглушка
try:
    from realtime.client import ChatClient
    HAS_WS = True
except Exception:
    HAS_WS = False


STATUS_CHOICES = ("Новая", "В работе", "Ожидает клиента", "Ожидает оператора", "Закрыта")


class MessageBubble(QFrame):
    def __init__(self, message_data, is_user=True):
        super().__init__()
        self.message_data = message_data
        self.is_user = is_user
        self.setup_ui()
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        self.message_label = QLabel(self.message_data["text"])
        self.message_label.setWordWrap(True)
        self.message_label.setFont(QFont("Arial", 10))

        info_layout = QHBoxLayout()
        self.time_label = QLabel(self.message_data["time"])
        self.time_label.setFont(QFont("Arial", 8))

        info_layout.addWidget(self.time_label)

        if self.is_user:
            self.status_label = QLabel("✓✓" if self.message_data.get("delivered", True) else "✓")
            self.status_label.setFont(QFont("Arial", 8))
            info_layout.addWidget(self.status_label)
        else:
            self.operator_label = QLabel(self.message_data.get("operator", "Поддержка"))
            self.operator_label.setFont(QFont("Arial", 8))
            info_layout.addWidget(self.operator_label)

        layout.addWidget(self.message_label)
        layout.addLayout(info_layout)

    def apply_theme(self):
        theme_data = theme_manager.get_theme_styles()
        colors = theme_data["colors"]

        if self.is_user:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["user_message"]};
                    border-radius: 12px;
                    color: white;
                    max-width: 360px;
                }}
            """)
            self.time_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
            if hasattr(self, 'status_label'):
                self.status_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["operator_message"]};
                    border-radius: 12px;
                    color: {colors["text_primary"]};
                    max-width: 360px;
                    border: 1px solid {colors["border"]};
                }}
            """)
            self.time_label.setStyleSheet(f"color: {colors['text_muted']};")
            if hasattr(self, 'operator_label'):
                self.operator_label.setStyleSheet(f"color: {colors['success']}; font-weight: bold;")


class AttachmentBubble(QFrame):
    def __init__(self, attach_data: dict, time_text: str, is_user=True):
        super().__init__()
        self.attach_data = attach_data  # keys: path, name, size, is_image
        self.is_user = is_user
        self.time_text = time_text
        self.setup_ui()
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

    def setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(6)

        # Превью
        self.preview = QLabel()
        self.preview.setScaledContents(False)

        if self.attach_data.get("is_image"):
            pix = QPixmap(self.attach_data["path"])
            if not pix.isNull():
                max_w = 320
                if pix.width() > max_w:
                    pix = pix.scaledToWidth(max_w, Qt.SmoothTransformation)
                self.preview.setPixmap(pix)
        else:
            self.preview.setText("📎")

        # Имя файла + размер
        name = self.attach_data.get("name", os.path.basename(self.attach_data["path"]))
        size = self.attach_data.get("size", "")
        self.name_label = QLabel(f"{name} {f'• {size}' if size else ''}")
        self.name_label.setWordWrap(True)
        self.name_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # Низ: время (+ для user — delivered)
        bottom = QHBoxLayout()
        self.time_label = QLabel(self.time_text)
        self.time_label.setFont(QFont("Arial", 8))
        bottom.addWidget(self.time_label)
        if self.is_user:
            self.status_label = QLabel("✓✓")
            self.status_label.setFont(QFont("Arial", 8))
            bottom.addWidget(self.status_label)
        bottom.addStretch()

        lay.addWidget(self.preview)
        lay.addWidget(self.name_label)
        lay.addLayout(bottom)

        # Клик по пузырю — открыть файл
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.attach_data["path"]))
        return super().mousePressEvent(event)

    def apply_theme(self):
        colors = theme_manager.get_theme_styles()["colors"]
        if self.is_user:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["user_message"]};
                    border-radius: 12px;
                    color: white;
                    max-width: 360px;
                }}
                QLabel {{ color: white; }}
            """)
            self.time_label.setStyleSheet("color: rgba(255,255,255,0.75);")
            if hasattr(self, 'status_label'):
                self.status_label.setStyleSheet("color: rgba(255,255,255,0.85);")
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["operator_message"]};
                    border-radius: 12px;
                    color: {colors["text_primary"]};
                    max-width: 360px;
                    border: 1px solid {colors["border"]};
                }}
            """)
            self.time_label.setStyleSheet(f"color: {colors['text_muted']};")



class ChatArea(QScrollArea):
    files_dropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.messages = []
        self.apply_theme()
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.backend_api = BackendAgentAPI()
        self.backend_rooms = {}  # local_chat_id -> backend room_id
        theme_manager.theme_changed.connect(self.apply_theme)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        paths = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                paths.append(url.toLocalFile())
        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def setup_ui(self):
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setSpacing(10)
        self.chat_layout.setContentsMargins(15, 15, 15, 15)
        self.chat_layout.addStretch()

        self.setWidget(self.chat_widget)

    def apply_theme(self):
        theme_data = theme_manager.get_theme_styles()
        colors = theme_data["colors"]

        self.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {colors["background"]};
            }}
            QScrollBar:vertical {{
                background-color: {colors["surface_alt"]};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {colors["border"]};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {colors["text_muted"]};
            }}
        """)

    def clear_messages(self):
        # Удаляем все, кроме финального stretch
        for i in range(self.chat_layout.count() - 2, -1, -1):
            item = self.chat_layout.itemAt(i)
            w = item.widget()
            if w:
                w.setParent(None)
        self.messages.clear()

    def load_messages(self, messages):
        self.clear_messages()
        for msg in messages:
            if "attachment" in msg:
                self.add_attachment(msg["attachment"], is_user=(msg.get("sender") == "user"), time_text=msg.get("time"))
            else:
                is_user = (msg.get("sender") == "user")
                self.add_message(msg.get("text", ""), is_user=is_user, operator=msg.get("operator"))

    def add_attachment(self, attach_data: dict, is_user=True, time_text=None):
        if not time_text:
            time_text = QDateTime.currentDateTime().toString("hh:mm")
        bubble = AttachmentBubble(attach_data, time_text, is_user)

        container = QWidget()
        cl = QHBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        if is_user:
            cl.addStretch(); cl.addWidget(bubble)
        else:
            cl.addWidget(bubble); cl.addStretch()

        self.chat_layout.insertWidget(self.chat_layout.count() - 1, container)
        QTimer.singleShot(100, self.scroll_to_bottom)

        # локальная модель (для автоскролла и простых сценариев)
        self.messages.append({"attachment": attach_data, "time": time_text})


    def add_message(self, text, is_user=True, operator=None):
        current_time = QDateTime.currentDateTime().toString("hh:mm")

        message_data = {
            "text": text,
            "time": current_time,
            "delivered": True
        }
        if not is_user and operator:
            message_data["operator"] = operator

        bubble = MessageBubble(message_data, is_user)

        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        if is_user:
            container_layout.addStretch()
            container_layout.addWidget(bubble)
        else:
            container_layout.addWidget(bubble)
            container_layout.addStretch()

        self.chat_layout.insertWidget(self.chat_layout.count() - 1, container)
        QTimer.singleShot(100, self.scroll_to_bottom)

        self.messages.append(message_data)

    def scroll_to_bottom(self):
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


class HistoryDialog(QDialog):
    """
    Простая история чатов: список с подсветкой статусов, открытие по двойному клику,
    удаление по кнопке/контекстному меню.
    """
    def __init__(self, chats, on_open, on_delete, parent=None):
        super().__init__(parent)
        self.setWindowTitle("История чатов")
        self.resize(520, 420)
        self.on_open = on_open
        self.on_delete = on_delete
        self.chats = list(chats)  # локальная копия

        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.list_widget.itemDoubleClicked.connect(self._open_selected)

        # Контекстное меню
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)

        # Кнопки
        buttons = QHBoxLayout()
        self.open_btn = QPushButton("Открыть")
        self.del_btn = QPushButton("Удалить")
        self.close_btn = QPushButton("Закрыть")

        self.open_btn.clicked.connect(self._open_selected)
        self.del_btn.clicked.connect(self._delete_selected)
        self.close_btn.clicked.connect(self.accept)

        buttons.addStretch()
        buttons.addWidget(self.open_btn)
        buttons.addWidget(self.del_btn)
        buttons.addWidget(self.close_btn)

        layout.addWidget(self.list_widget)
        layout.addLayout(buttons)

        self._reload()

    def _status_emoji(self, status):
        mapping = {
            "Новая": "🆕",
            "В работе": "🟢",
            "Ожидает клиента": "🟡",
            "Закрыта": "⚪"
        }
        return mapping.get(status, "💬")

    def _status_color(self, status, colors):
        if status == "Новая":
            return colors["primary"]
        if status == "В работе":
            return colors["success"]
        if status == "Ожидает клиента":
            return colors["warning"]
        if status == "Закрыта":
            return colors["text_muted"]
        return colors["text_secondary"]

    def _reload(self):
        self.list_widget.clear()
        colors = theme_manager.get_theme_styles()["colors"]

        # новее — выше
        def sort_key(ch):
            return ch.get("updated_at", ""), ch.get("id", "")
        for chat in sorted(self.chats, key=sort_key, reverse=True):
            item = QListWidgetItem()
            text = f"{self._status_emoji(chat['status'])} [{chat['status']}] {chat['id']} — {chat['title']} • {chat.get('updated_at','')}"
            item.setText(text)
            # Цвет по статусу
            item.setForeground(Qt.black if theme_manager.get_current_theme() == ThemeType.LIGHT else Qt.white)
            # Добавим легкую подсветку в зависимости от статуса через background (не aggressively ярко)
            item.setData(Qt.UserRole, chat["id"])
            self.list_widget.addItem(item)

    def _selected_chat_id(self):
        it = self.list_widget.currentItem()
        if not it:
            return None
        return it.data(Qt.UserRole)

    def _open_selected(self):
        chat_id = self._selected_chat_id()
        if not chat_id:
            return
        if self.on_open:
            self.on_open(chat_id)
        self.accept()

    def _delete_selected(self):
        chat_id = self._selected_chat_id()
        if not chat_id:
            return
        if QMessageBox.question(self, "Удалить чат",
                                "Удалить выбранный чат? Это действие необратимо.",
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            # Удаляем локально и через колбэк
            self.chats = [c for c in self.chats if c["id"] != chat_id]
            if self.on_delete:
                self.on_delete(chat_id)
            self._reload()

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        open_action = menu.addAction("Открыть")
        del_action = menu.addAction("Удалить")
        act = menu.exec_(self.list_widget.mapToGlobal(pos))
        if act == open_action:
            self._open_selected()
        elif act == del_action:
            self._delete_selected()


class MainWindow(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.main_toolbar = None

        # Состояние чатов пользователя
        self.chats = []           # список словарей чатов конкретного пользователя
        self.chats_by_id = {}     # индекс по id
        self.active_chat = None   # текущая заявка

        theme_manager.theme_changed.connect(self.apply_theme)

        self.setup_ui()
        self.setup_toolbar()
        self.load_user_chats()
        self.build_left_list()
        self.show_empty_state()
        self.agent_ids = read_agent_ids()
        self._init_realtime()
        self.setup_statusbar()
        self.apply_theme()

    def _init_realtime(self):
        import os
        ws_uri = os.getenv("CHAT_WS_URL")  # например ws://127.0.0.1:8765
        if HAS_WS and ws_uri:
            self.ws = ChatClient(
                uri=ws_uri,
                agent_instance_id=self.agent_ids.instance_id,
                agent_operator_id=self.agent_ids.operator_id
            )
            self.ws.state_changed.connect(
                lambda s: self.connection_status.setText("🟢 Подключен" if s == "connected" else "🔴 Отключен")
            )
            self.ws.message_received.connect(self._on_ws_message)
            self.ws.start()
        else:
            # Фоллбек на заглушку
            self.rtc = FakeRealtimeClient(self.user_data["id"])
            self.rtc.connected.connect(lambda: self.connection_status.setText("🟢 Подключен"))
            self.rtc.disconnected.connect(lambda: self.connection_status.setText("🔴 Отключен"))
            self.rtc.message_received.connect(self._on_rt_message)
            self.rtc.status_changed.connect(self._on_rt_status)
            self.rtc.connect()

    def _ws_start_chat(self, chat_id: str):
        if hasattr(self, "ws") and self.ws:
            self.ws.start_chat(chat_id, self.user_data["id"])

    def _on_rt_message(self, chat_id, msg):
        # дополним временем
        msg.setdefault("time", QDateTime.currentDateTime().toString("hh:mm"))
        chat = self.chats_by_id.get(chat_id)
        if not chat:
            return
        chat["messages"].append(msg)
        repo.add_message(chat_id, sender=msg.get("sender", "operator"), text=msg.get("text"),
                         operator=msg.get("operator"), time_str=msg.get("time"))
        if chat.get("status") != "В работе":
            chat["status"] = "В работе"
            repo.update_chat_status(chat_id, "В работе")
        chat["updated_at"] = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm")
        self.chat_list.upsert_chat(chat)
        if self.active_chat and self.active_chat["id"] == chat_id:
            self.chat_area.add_message(msg["text"], is_user=(msg.get("sender") == "user"), operator=msg.get("operator"))
            self.update_header_for_chat()

    def _on_ws_message(self, data: dict):
        if data.get("type") != "message":
            return
        chat_id = data.get("dialog_id")
        if not chat_id:
            return
        # Игнорируем эхо-пакеты от пользователя (мы тут ждём только ответы оператора)
        if data.get("sender") == "user":
            return

        msg = {
            "sender": "operator",
            "operator": data.get("operator_name", "Оператор"),
            "text": data.get("text", ""),
            "time": QDateTime.currentDateTime().toString("hh:mm")
        }
        chat = self.chats_by_id.get(chat_id)
        if not chat:
            return

        chat["messages"].append(msg)
        repo.add_message(chat_id, sender="operator", text=msg["text"], operator=msg["operator"], time_str=msg["time"])
        if chat.get("status") != "В работе":
            chat["status"] = "В работе"
            repo.update_chat_status(chat_id, "В работе")
        chat["updated_at"] = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm")
        self.chat_list.upsert_chat(chat)

        if self.active_chat and self.active_chat["id"] == chat_id:
            self.chat_area.add_message(msg["text"], is_user=False, operator=msg["operator"])
            self.update_header_for_chat()

    def _on_rt_status(self, chat_id, status):
        self.change_status(chat_id, status)

    def setup_ui(self):
        self.setWindowTitle(f"Чат поддержки - {self.user_data['name']}")
        self.setGeometry(100, 100, 900, 640)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.header = self.create_header()
        main_layout.addWidget(self.header)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter, 1)

        # LEFT: панель со списком, поиском и массовыми действиями
        self.left_panel = self.create_left_panel()

        # CENTER: стек (пустое состояние / чат)
        self.center_stack = QStackedWidget()

        # Пустое состояние
        self.empty_state = self.create_empty_state()
        self.center_stack.addWidget(self.empty_state)

        # Страница чата
        self.chat_page = QWidget()
        chat_layout = QVBoxLayout(self.chat_page)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        self.chat_area = ChatArea()
        self.chat_area.files_dropped.connect(self.on_files_dropped)
        chat_layout.addWidget(self.chat_area, 1)
        self.input_panel = self.create_input_panel()
        chat_layout.addWidget(self.input_panel)
        self.center_stack.addWidget(self.chat_page)

        # RIGHT: боковая панель
        self.sidebar = self.create_sidebar()

        splitter.addWidget(self.left_panel)
        splitter.addWidget(self.center_stack)
        splitter.addWidget(self.sidebar)
        splitter.setSizes([280, 580, 240])

        # индексы
        self.CENTER_EMPTY = 0
        self.CENTER_CHAT = 1

    def _human_size(self, num):
        for unit in ['Б','КБ','МБ','ГБ','ТБ']:
            if abs(num) < 1024.0:
                return f"{num:.1f} {unit}"
            num /= 1024.0
        return f"{num:.1f} ПБ"

    def _build_attachment_data(self, path: str):
        name = os.path.basename(path)
        try:
            size = self._human_size(os.path.getsize(path))
        except Exception:
            size = ""
        ext = os.path.splitext(name)[1].lower()
        is_image = ext in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
        return {"path": path, "name": name, "size": size, "is_image": is_image}

    def on_files_dropped(self, paths):
        if not self.active_chat:
            # если нет активного чата — создаем новый автоматически
            self.create_new_chat()
        for p in paths:
            attach = self._build_attachment_data(p)
            self.chat_area.add_attachment(attach, is_user=True)
            msg_time = QDateTime.currentDateTime().toString("hh:mm")
            self.active_chat["messages"].append({"sender": "user", "attachment": attach, "time": msg_time})
            repo.add_message(self.active_chat["id"], sender="user", attachment=attach, time_str=msg_time)
        # статус
        self.active_chat["status"] = "Ожидает оператора"
        self.active_chat["updated_at"] = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm")
        self.update_header_for_chat()
        self.chat_list.upsert_chat(self.active_chat)
        self._rt_send("[attachment]")

        room_id = self.backend_rooms.get(self.active_chat["id"])
        if room_id:
            paths = list(paths)  # уже список

            def _send_files():
                code, resp = self.backend_api.send_message(room_id, self.agent_ids.instance_id, message="[attachment]",
                                                           files=paths)
                if not (code and 200 <= code < 300):
                    print("Backend send_message(files) error:", resp)

            threading.Thread(target=_send_files, daemon=True).start()


    def create_left_panel(self):
        panel = QFrame()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(8)

        # Поиск
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по названию или ID...")
        self.search_input.textChanged.connect(self.apply_chat_filters)

        # Фильтр статуса
        from PySide6.QtWidgets import QComboBox, QHBoxLayout
        self.status_filter = QComboBox()
        self.status_filter.addItem("Все статусы")
        for st in STATUS_CHOICES:
            self.status_filter.addItem(st)
        self.status_filter.currentIndexChanged.connect(self.apply_chat_filters)

        # Массовые действия
        self.bulk_close_btn = QPushButton("✔ Закрыть выбранные")
        self.bulk_delete_btn = QPushButton("🗑 Удалить выбранные")
        self.bulk_close_btn.clicked.connect(self.bulk_close_selected)
        self.bulk_delete_btn.clicked.connect(self.bulk_delete_selected)

        # Список
        self.chat_list = ChatList()
        self.chat_list.chat_selected.connect(self.set_active_chat)
        self.chat_list.chat_rename.connect(self.rename_chat)
        self.chat_list.chat_delete.connect(self.delete_chat)
        self.chat_list.chat_change_status.connect(self.change_status)

        lay.addWidget(self.search_input)
        lay.addWidget(self.status_filter)
        lay.addWidget(self.bulk_close_btn)
        lay.addWidget(self.bulk_delete_btn)
        lay.addWidget(self.chat_list, 1)
        return panel

    def bulk_close_selected(self):
        ids = self.chat_list.get_selected_ids()
        if not ids:
            return
        if QMessageBox.question(self, "Закрыть заявки", f"Закрыть выбранные ({len(ids)}) заявки?",
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        for cid in ids:
            self.change_status(cid, "Закрыта")
        self.apply_chat_filters()

    def bulk_delete_selected(self):
        ids = self.chat_list.get_selected_ids()
        if not ids:
            return
        if QMessageBox.question(self, "Удалить заявки", f"Удалить выбранные ({len(ids)}) заявки?",
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        for cid in ids:
            self.delete_chat(cid)
        self.apply_chat_filters()


    def apply_chat_filters(self):
        query = (self.search_input.text() or "").strip().lower()
        status = self.status_filter.currentText()
        filtered = []
        for c in self.chats:
            if status != "Все статусы" and c.get("status") != status:
                continue
            if query and (query not in c["title"].lower() and query not in c["id"].lower()):
                continue
            filtered.append(c)
        self.chat_list.set_chats(filtered)
        # подсветим активный, если он в фильтре
        if self.active_chat and any(c["id"] == self.active_chat["id"] for c in filtered):
            self.chat_list.select_chat(self.active_chat["id"])


    def create_empty_state(self):
        panel = QFrame()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addStretch()
        title = QLabel("Нет активного диалога")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        subtitle = QLabel("Выберите диалог слева или создайте новую заявку")
        subtitle.setAlignment(Qt.AlignCenter)
        btn = QPushButton("🆕 Создать заявку")
        btn.setFixedSize(220, 44)
        btn.clicked.connect(self.create_new_chat)

        lay.addWidget(title)
        lay.addWidget(subtitle)
        hl = QHBoxLayout()
        hl.addStretch()
        hl.addWidget(btn)
        hl.addStretch()
        lay.addLayout(hl)
        lay.addStretch()
        return panel

    def show_empty_state(self):
        self.active_chat = None
        self.center_stack.setCurrentIndex(self.CENTER_EMPTY)
        self.update_header_for_chat()

    def build_left_list(self):
        self.chat_list.set_chats(self.chats)

    def create_header(self):
        header = QFrame()
        header.setFixedHeight(68)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(14)

        self.avatar_label = QLabel(self.user_data["avatar"])
        self.avatar_label.setStyleSheet("font-size: 22px;")
        self.avatar_label.setFixedSize(44, 44)
        self.avatar_label.setAlignment(Qt.AlignCenter)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self.name_label = QLabel(self.user_data["name"])
        self.name_label.setFont(QFont("Arial", 12, QFont.Bold))

        # Блок с ID пользователя + текущая заявка (ID + статус)
        sub_layout = QHBoxLayout()
        sub_layout.setSpacing(8)
        self.details_label = QLabel(f"ID: {self.user_data['id']} • {self.user_data['status']}")
        self.details_label.setFont(QFont("Arial", 9))

        self.ticket_label = QLabel("")            # NEW: CH-XXXX
        self.ticket_label.setFont(QFont("Arial", 9, QFont.Bold))
        self.ticket_status_label = QLabel("")     # NEW: Чип статуса
        self.ticket_status_label.setFont(QFont("Arial", 9, QFont.Bold))
        self.ticket_status_label.setContentsMargins(8, 2, 8, 2)

        sub_layout.addWidget(self.details_label)
        sub_layout.addSpacing(10)
        sub_layout.addWidget(self.ticket_label)
        sub_layout.addWidget(self.ticket_status_label)
        sub_layout.addStretch()

        info_layout.addWidget(self.name_label)
        info_layout.addLayout(sub_layout)

        self.connection_status = QLabel("🟢 Подключен")
        self.connection_status.setFont(QFont("Arial", 10))

        layout.addWidget(self.avatar_label)
        layout.addLayout(info_layout, 1)
        layout.addWidget(self.connection_status)

        return header

    def create_input_panel(self):
        panel = QFrame()
        panel.setFixedHeight(84)

        layout = QHBoxLayout(panel)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)

        self.message_input = QTextEdit()
        self.message_input.setFixedHeight(56)
        self.message_input.setPlaceholderText("Введите ваше сообщение...")

        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(6)

        self.attach_btn = QPushButton("📎")
        self.attach_btn.setFixedSize(38, 26)
        self.attach_btn.setToolTip("Прикрепить файл")
        self.attach_btn.clicked.connect(self.attach_file)

        self.send_btn = QPushButton("Отправить")
        self.send_btn.setFixedSize(92, 26)
        self.send_btn.clicked.connect(self.send_message)

        buttons_layout.addWidget(self.attach_btn)
        buttons_layout.addWidget(self.send_btn)

        layout.addWidget(self.message_input, 1)
        layout.addLayout(buttons_layout)

        # Отправка по Enter (без Shift)
        self.message_input.keyPressEvent = self.handle_key_press

        return panel

    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setMaximumWidth(270)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(16)

        self.sidebar_title = QLabel("Информация")
        self.sidebar_title.setFont(QFont("Arial", 13, QFont.Bold))

        self.user_info = QLabel(f"""
        <b>Контактные данные:</b><br>
        📧 {self.user_data['email']}<br>
        📱 {self.user_data['phone']}<br><br>
        <b>Статус:</b> {self.user_data['status']}<br>
        <b>ID:</b> {self.user_data['id']}
        """)
        self.user_info.setWordWrap(True)

        self.operators_label = QLabel("Операторы онлайн:")
        self.operators_label.setFont(QFont("Arial", 11, QFont.Bold))

        self.operators_list = QListWidget()
        self.operators_list.setMaximumHeight(120)
        self.operators_list.addItem("👩‍💼 Петрова Аня")
        self.operators_list.addItem("👨‍💻 Сидоров Михаил")
        self.operators_list.addItem("👩‍💻 Головач Лена")

        self.actions_label = QLabel("Действия:")
        self.actions_label.setFont(QFont("Arial", 11, QFont.Bold))

        self.history_btn = QPushButton("📋 История чатов")
        self.settings_btn = QPushButton("⚙️ Настройки")
        self.logout_btn = QPushButton("🚪 Выход")

        # NEW: быстрый доступ к "Новый чат" через контекст меню правой панели (не обязательно)
        self.new_chat_btn = QPushButton("🆕 Новый чат")

        self.history_btn.clicked.connect(self.open_history)
        self.new_chat_btn.clicked.connect(self.create_new_chat)
        self.logout_btn.clicked.connect(self.logout)

        layout.addWidget(self.sidebar_title)
        layout.addWidget(self.user_info)
        layout.addWidget(self.operators_label)
        layout.addWidget(self.operators_list)
        layout.addWidget(self.actions_label)
        layout.addWidget(self.new_chat_btn)
        layout.addWidget(self.history_btn)
        layout.addWidget(self.settings_btn)
        layout.addWidget(self.logout_btn)
        layout.addStretch()

        return sidebar

    def setup_toolbar(self):
        self.main_toolbar = QToolBar()
        self.addToolBar(self.main_toolbar)

        new_chat_action = QAction("🆕 Новый чат", self)
        rename_action = QAction("✏️ Переименовать", self)
        settings_action = QAction("⚙️ Настройки", self)

        theme_toggle_action = QAction("🌙/☀️ Тема", self)
        theme_toggle_action.setShortcut('Ctrl+T')
        theme_toggle_action.triggered.connect(theme_manager.toggle_theme)

        # подключаем действия
        new_chat_action.triggered.connect(self.create_new_chat)
        rename_action.triggered.connect(lambda: self.rename_chat())
        settings_action.triggered.connect(self.open_settings_placeholder)

        self.main_toolbar.addAction(new_chat_action)
        self.main_toolbar.addSeparator()
        self.main_toolbar.addAction(rename_action)
        self.main_toolbar.addAction(settings_action)
        self.main_toolbar.addSeparator()
        self.main_toolbar.addAction(theme_toggle_action)

    def setup_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к отправке сообщений")

    # ---------- Работа с чатами ----------

    def load_user_chats(self):
        """Загружаем чаты конкретного пользователя из тестовых данных"""
        user_id = self.user_data["id"]
        self.chats = repo.load_user_chats(user_id)
        self.chats_by_id = {c["id"]: c for c in self.chats}

    def select_initial_chat(self):
        """Выбираем начальный чат: сначала 'В работе', затем 'Новая', иначе первый или создаем новый"""
        chat = None
        for st in ("В работе", "Новая"):
            for c in self.chats:
                if c["status"] == st:
                    chat = c
                    break
            if chat:
                break
        if not chat and self.chats:
            chat = self.chats[0]
        if not chat:
            chat = self._create_chat_object(title="Общая заявка", status="Новая")
            self._add_chat(chat)
        self.set_active_chat(chat["id"])

    def set_active_chat(self, chat_id):
        chat = repo.get_chat(chat_id)
        if not chat:
            return
        self.chats_by_id[chat_id] = chat
        self.active_chat = chat
        self.update_header_for_chat()
        self.chat_area.load_messages(self.active_chat.get("messages", []))
        self.center_stack.setCurrentIndex(self.CENTER_CHAT)
        self.chat_list.select_chat(chat_id)
        self._subscribe_ws(chat_id)

    def create_new_chat(self):
        title, ok = self._ask_new_chat_title()
        if not ok:
            return
        chat = repo.create_chat(self.user_data["id"], title or "Новая заявка")
        self._add_chat(chat)
        self.chat_list.upsert_chat(chat)
        self.set_active_chat(chat["id"])

        def _send_start_backend():
            code, payload = self.backend_api.start_chat(
                instance_uid=self.agent_ids.instance_id,
                crm_operator_fio=self.agent_ids.operator_id,
                title=title or "Новая заявка",
                message=""
            )
            if code and 200 <= code < 300:
                room = (payload or {}).get("room") or {}
                room_id = room.get("id")
                if room_id:
                    self.backend_rooms[chat["id"]] = room_id
            else:
                print("Backend start_chat error:", payload)

        threading.Thread(target=_send_start_backend, daemon=True).start()

        self._ws_start_chat(chat["id"])
        self.status_bar.showMessage(f"Создан новый чат {chat['id']}")

    def _ask_new_chat_title(self):
        return QInputDialog.getText(self, "Новый чат", "Тема обращения:", text="Новая заявка")

    def _create_chat_object(self, title, status="Новая"):
        new_id = self._next_chat_id()
        now_dt = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm")
        return {
            "id": new_id,
            "user_id": self.user_data["id"],
            "title": title,
            "status": status,
            "created_at": now_dt,
            "updated_at": now_dt,
            "messages": [
                {"sender": "operator", "operator": "Головач Лена", "text": "Здравствуйте! Чем можем помочь?", "time": QDateTime.currentDateTime().toString("hh:mm")}
            ]
        }

    def _next_chat_id(self):
        existing = [c["id"] for c in self.chats_by_id.values()]
        max_n = 0
        for cid in existing:
            try:
                n = int(cid.split("-")[1])
                max_n = max(max_n, n)
            except Exception:
                pass
        return f"CH-{max_n + 1:04d}"

    def _add_chat(self, chat):
        self.chats.append(chat)
        self.chats_by_id[chat["id"]] = chat

    def delete_chat(self, chat_id):
        if chat_id not in self.chats_by_id:
            return
        repo.delete_chat(chat_id)
        deleting_active = (self.active_chat and self.active_chat["id"] == chat_id)
        self.chats = [c for c in self.chats if c["id"] != chat_id]
        self.chats_by_id.pop(chat_id, None)
        self.chat_list.remove_chat(chat_id)
        if deleting_active:
            if self.chats:
                self.set_active_chat(self.chats[0]["id"])
            else:
                self.show_empty_state()

    def open_history(self):
        dlg = HistoryDialog(
            chats=self.chats,
            on_open=self.set_active_chat,
            on_delete=self.delete_chat,
            parent=self
        )
        dlg.exec()

    def open_settings_placeholder(self):
        dlg = SettingsDialog(self)
        dlg.exec()

    def _subscribe_ws(self, chat_id: str):
        if hasattr(self, "ws") and self.ws:
            room = f"dialog:{chat_id}"
            self.ws.subscribe(room)

    def _rt_send(self, text: str):
        # Отправка через WS или заглушку
        if self.active_chat is None:
            return
        if hasattr(self, "ws") and self.ws:
            room = f"dialog:{self.active_chat['id']}"
            self.ws.send_user_message(room, self.active_chat["id"], self.user_data["id"], text)
        elif hasattr(self, "rtc"):
            self.rtc.send_message(self.active_chat["id"], text)

    # ---------- Отрисовка и статусы ----------

    def get_status_color(self, status):
        colors = theme_manager.get_theme_styles()["colors"]
        if status == "Новая":
            return colors["primary"]
        if status == "В работе":
            return colors["success"]
        if status == "Ожидает клиента":
            return colors["warning"]
        if status == "Закрыта":
            return colors["text_muted"]
        if status == "Ожидает оператора":
            return colors["warning"]
        return colors["text_secondary"]

    def update_header_for_chat(self):
        if not self.active_chat:
            self.ticket_label.setText("")
            self.ticket_status_label.setText("")
            return
        self.ticket_label.setText(self.active_chat["id"])
        self.ticket_status_label.setText(self.active_chat["status"])
        # Стили чипа статуса будут заданы в apply_theme()

    # ---------- Ввод/отправка сообщений ----------

    def handle_key_press(self, event):
        if event.key() == Qt.Key_Return and not event.modifiers() == Qt.ShiftModifier:
            self.send_message()
            event.accept()
        else:
            QTextEdit.keyPressEvent(self.message_input, event)

    def send_message(self):
        text = self.message_input.toPlainText().strip()
        if not text:
            return
        if not self.active_chat:
            self.show_empty_state()
            return

        self.chat_area.add_message(text, is_user=True)
        self.message_input.clear()

        msg_time = QDateTime.currentDateTime().toString("hh:mm")
        self.active_chat["messages"].append({"sender": "user", "text": text, "time": msg_time})
        # Новый статус
        self.active_chat["status"] = "Ожидает оператора"
        self.active_chat["updated_at"] = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm")
        repo.add_message(self.active_chat["id"], sender="user", text=text, time_str=msg_time)
        repo.update_chat_status(self.active_chat["id"], "Ожидает оператора")
        self.update_header_for_chat()
        self.chat_list.upsert_chat(self.active_chat)

        # Отправка через WS или заглушку
        self._rt_send(text)

        room_id = self.backend_rooms.get(self.active_chat["id"])
        if room_id:
            def _send_msg():
                code, resp = self.backend_api.send_message(room_id, self.agent_ids.instance_id, message=text)
                if not (code and 200 <= code < 300):
                    print("Backend send_message error:", resp)

            threading.Thread(target=_send_msg, daemon=True).start()

        self.status_bar.showMessage(f"Сообщение отправлено в {QDateTime.currentDateTime().toString('hh:mm:ss')}")

    def attach_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл",
            "",
            "Все файлы (*.*)"
        )
        if file_path:
            self.on_files_dropped([file_path])

    def logout(self):
        reply = QMessageBox.question(
            self,
            'Подтверждение выхода',
            'Вы действительно хотите выйти из системы?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.close()

    def apply_theme(self):
        if hasattr(self, 'empty_state'):
            # никаких спец. стилей — наследуется
            pass
        theme_data = theme_manager.get_theme_styles()
        colors = theme_data["colors"]
        styles = theme_data["styles"]

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {colors["background"]};
                color: {colors["text_primary"]};
            }}
        """)

        if hasattr(self, 'header'):
            self.header.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["surface"]};
                    border-bottom: 1px solid {colors["border"]};
                }}
            """)
            self.name_label.setStyleSheet(f"color: {colors['text_primary']};")
            self.details_label.setStyleSheet(f"color: {colors['text_muted']};")
            self.connection_status.setStyleSheet(f"color: {colors['success']};")

            # Чип статуса и тикет
            if self.active_chat:
                st_color = self.get_status_color(self.active_chat["status"])
            else:
                st_color = colors["text_muted"]

            self.ticket_label.setStyleSheet(f"color: {colors['text_secondary']};")
            self.ticket_status_label.setStyleSheet(f"""
                color: white;
                background-color: {st_color};
                border-radius: 10px;
                padding: 2px 8px;
            """)

        if hasattr(self, 'input_panel'):
            self.input_panel.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["surface"]};
                    border-top: 1px solid {colors["border"]};
                }}
            """)

            self.message_input.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {colors["surface_alt"]};
                    border: 2px solid {colors["border"]};
                    border-radius: 8px;
                    padding: 8px;
                    font-size: 12px;
                    color: {colors["text_primary"]};
                }}
                QTextEdit:focus {{
                    border: 2px solid {colors["primary"]};
                }}
            """)

            button_style = f"""
                QPushButton {{
                    background-color: {colors["primary"]};
                    border: none;
                    border-radius: 6px;
                    color: white;
                    font-weight: bold;
                    font-size: 11px;
                    padding: 6px 10px;
                }}
                QPushButton:hover {{
                    background-color: {colors["primary_hover"]};
                }}
                QPushButton:pressed {{
                    background-color: {colors["primary_pressed"]};
                }}
            """
            self.send_btn.setStyleSheet(button_style)
            self.attach_btn.setStyleSheet(button_style)

        if hasattr(self, 'sidebar'):
            self.sidebar.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["surface"]};
                    border-left: 1px solid {colors["border"]};
                }}
            """)
            self.sidebar_title.setStyleSheet(f"""
                color: {colors['text_primary']}; 
                border-bottom: 1px solid {colors['border']}; 
                padding-bottom: 6px;
            """)
            # Увеличили шрифты правого меню
            self.user_info.setStyleSheet(f"color: {colors['text_secondary']}; font-size: 12px;")
            self.operators_label.setStyleSheet(f"color: {colors['text_primary']};")
            self.actions_label.setStyleSheet(f"color: {colors['text_primary']};")

            self.operators_list.setStyleSheet(f"""
                QListWidget {{
                    background-color: {colors["surface_alt"]};
                    border: 1px solid {colors["border"]};
                    border-radius: 6px;
                    font-size: 11px;
                    color: {colors["text_secondary"]};
                }}
                QListWidget::item {{
                    padding: 6px;
                    border-bottom: 1px solid {colors["border"]};
                }}
                QListWidget::item:hover {{
                    background-color: {colors["primary"]};
                    color: white;
                }}
            """)

            sidebar_button_style = f"""
                QPushButton {{
                    background-color: {colors["surface_alt"]};
                    border: 1px solid {colors["border"]};
                    border-radius: 6px;
                    padding: 8px;
                    text-align: left;
                    font-size: 11px;
                    color: {colors["text_primary"]};
                }}
                QPushButton:hover {{
                    background-color: {colors["primary"]};
                    border: 1px solid {colors["primary"]};
                    color: white;
                }}
                QPushButton:pressed {{
                    background-color: {colors["primary_pressed"]};
                }}
            """
            for btn in [self.history_btn, self.settings_btn, self.logout_btn, self.new_chat_btn]:
                btn.setStyleSheet(sidebar_button_style)

        if hasattr(self, 'main_toolbar') and self.main_toolbar:
            self.main_toolbar.setStyleSheet(f"""
                QToolBar {{
                    background-color: {colors["surface_alt"]};
                    border-bottom: 1px solid {colors["border"]};
                    spacing: 6px;
                    padding: 6px;
                }}
                QToolBar QToolButton {{
                    color: {colors["text_primary"]};
                    font-size: 11px;
                    padding: 6px 10px;
                    border: none;
                    border-radius: 6px;
                }}
                QToolBar QToolButton:hover {{
                    background-color: {colors["primary"]};
                    color: white;
                }}
            """)

        if hasattr(self, 'status_bar'):
            self.status_bar.setStyleSheet(f"""
                QStatusBar {{
                    background-color: {colors["surface_alt"]};
                    color: {colors["text_secondary"]};
                    border-top: 1px solid {colors["border"]};
                    font-size: 10px;
                }}
            """)

        if hasattr(self, 'search_input'):
            self.search_input.setStyleSheet(styles["input"])
        if hasattr(self, 'status_filter'):
            # простой стиль под тему
            self.status_filter.setStyleSheet(f"""
                        QComboBox {{
                            background: {colors["surface_alt"]};
                            color: {colors["text_primary"]};
                            border: 1px solid {colors["border"]};
                            border-radius: 6px;
                            padding: 4px;
                        }}
                        QComboBox QAbstractItemView {{
                            background: {colors["surface"]};
                            color: {colors["text_primary"]};
                            selection-background-color: {colors["primary"]};
                        }}
                    """)

    def rename_chat(self, chat_id=None):
        if chat_id is None:
            chat_id = self.active_chat["id"] if self.active_chat else None
        if not chat_id:
            return
        chat = self.chats_by_id.get(chat_id)
        new_title, ok = QInputDialog.getText(self, "Переименовать заявку", "Название:", text=chat["title"])
        if ok and new_title.strip():
            chat["title"] = new_title.strip()
            chat["updated_at"] = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm")
            self.chat_list.upsert_chat(chat)
            repo.rename_chat(chat_id, chat["title"])
            if self.active_chat and self.active_chat["id"] == chat_id:
                self.update_header_for_chat()

    def change_status(self, chat_id, status):
        chat = self.chats_by_id.get(chat_id)
        if not chat:
            return
        chat["status"] = status
        chat["updated_at"] = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm")
        self.chat_list.upsert_chat(chat)
        if self.active_chat and self.active_chat["id"] == chat_id:
            self.update_header_for_chat()
            repo.update_chat_status(chat_id, status)
            self.apply_theme()

    def closeEvent(self, event):
        try:
            if hasattr(self, "ws") and self.ws:
                self.ws.stop()
            elif hasattr(self, "rtc"):
                self.rtc.disconnect()
        except Exception:
            pass
        super().closeEvent(event)


