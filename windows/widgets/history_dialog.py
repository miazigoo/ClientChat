from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                               QListWidget, QListWidgetItem, QPushButton,
                               QMenu, QMessageBox)
from PySide6.QtCore import Qt
from styles.theme_manager import theme_manager, ThemeType


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

        self.setup_ui()
        self._reload()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Список чатов
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

    def apply_theme(self):
        """Применение текущей темы к диалогу"""
        theme_data = theme_manager.get_theme_styles()
        colors = theme_data["colors"]
        styles = theme_data["styles"]

        # Основные стили диалога
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors["background"]};
                color: {colors["text_primary"]};
            }}
            QListWidget {{
                background-color: {colors["surface"]};
                border: 1px solid {colors["border"]};
                border-radius: 6px;
                color: {colors["text_primary"]};
                font-size: 11px;
            }}
            QListWidget::item {{
                padding: 8px;
                margin: 2px;
                border-radius: 4px;
            }}
            QListWidget::item:selected {{
                background-color: {colors["primary"]};
                color: white;
            }}
            QListWidget::item:hover {{
                background-color: {colors["surface_alt"]};
            }}
        """)

        # Стили кнопок
        button_style = styles["button"]
        for btn in [self.open_btn, self.del_btn, self.close_btn]:
            btn.setStyleSheet(button_style)

    def _status_emoji(self, status):
        mapping = {
            "Новая": "🆕",
            "В работе": "🟢",
            "Ожидает клиента": "🟡",
            "Ожидает оператора": "🟠",
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
        if status == "Ожидает оператора":
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
            emoji = self._status_emoji(chat['status'])
            status = chat['status']
            chat_id = chat['id']
            title = chat['title']
            updated = chat.get('updated_at', '')

            text = f"{emoji} [{status}] {chat_id} — {title} • {updated}"
            item.setText(text)

            # Цвет по статусу
            item.setForeground(Qt.black if theme_manager.get_current_theme() == ThemeType.LIGHT else Qt.white)
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

        reply = QMessageBox.question(
            self,
            "Удалить чат",
            "Удалить выбранный чат? Это действие необратимо.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Удаляем локально и через колбэк
            self.chats = [c for c in self.chats if c["id"] != chat_id]
            if self.on_delete:
                self.on_delete(chat_id)
            self._reload()

    def _show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)

        # Применяем тему к меню
        colors = theme_manager.get_theme_styles()["colors"]
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {colors["surface"]};
                color: {colors["text_primary"]};
                border: 1px solid {colors["border"]};
                border-radius: 4px;
            }}
            QMenu::item {{
                padding: 6px 12px;
            }}
            QMenu::item:selected {{
                background-color: {colors["primary"]};
                color: white;
            }}
        """)

        open_action = menu.addAction("Открыть")
        del_action = menu.addAction("Удалить")

        act = menu.exec_(self.list_widget.mapToGlobal(pos))
        if act == open_action:
            self._open_selected()
        elif act == del_action:
            self._delete_selected()
