from PySide6.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, Signal, QTimer, QDateTime
from styles.theme_manager import theme_manager
from .message_widgets import MessageBubble, AttachmentBubble


class ChatArea(QScrollArea):
    files_dropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.messages = []
        self.apply_theme()
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
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
            if item:
                w = item.widget()
                if w:
                    w.deleteLater()
                self.chat_layout.removeItem(item)
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
