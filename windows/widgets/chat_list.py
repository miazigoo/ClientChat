from PySide6.QtWidgets import QListWidget, QListWidgetItem, QMenu
from PySide6.QtCore import Qt, Signal, QSize
from styles.theme_manager import theme_manager

STATUS_CHOICES = ("Новая", "В работе", "Ожидает клиента", "Ожидает оператора", "Закрыта")

class ChatList(QListWidget):
    chat_selected = Signal(str)
    chat_rename = Signal(str)
    chat_delete = Signal(str)
    chat_change_status = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self.itemClicked.connect(self._on_item_clicked)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)
        self.chats_by_id = {}
        self.setMinimumWidth(260)
        self.setUniformItemSizes(True)
        self.setSpacing(2)
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    def get_selected_ids(self):
        return [it.data(Qt.UserRole) for it in self.selectedItems()]

    def apply_theme(self):
        colors = theme_manager.get_theme_styles()["colors"]
        self.setStyleSheet(f"""
            QListWidget {{
                background: {colors["surface"]};
                border-right: 1px solid {colors["border"]};
                outline: 0;
            }}
            QListWidget::item {{
                padding: 8px;
                margin: 2px 6px;
                border-radius: 8px;
                color: {colors["text_primary"]};
            }}
            QListWidget::item:selected {{
                background: {colors["primary"]};
                color: white;
            }}
            QListWidget::item:hover {{
                background: {colors["surface_alt"]};
            }}
        """)

    def set_chats(self, chats):
        self.clear()
        self.chats_by_id = {c["id"]: c for c in chats}
        for c in sorted(chats, key=lambda x: x.get("updated_at", ""), reverse=True):
            self._add_item(c)

    def upsert_chat(self, chat):
        self.chats_by_id[chat["id"]] = chat
        for i in range(self.count()):
            it = self.item(i)
            if it.data(Qt.UserRole) == chat["id"]:
                it.setText(self._format_text(chat))
                return
        self._add_item(chat)

    def remove_chat(self, chat_id):
        for i in range(self.count()):
            if self.item(i).data(Qt.UserRole) == chat_id:
                self.takeItem(i)
                break
        self.chats_by_id.pop(chat_id, None)

    def select_chat(self, chat_id):
        for i in range(self.count()):
            if self.item(i).data(Qt.UserRole) == chat_id:
                self.setCurrentRow(i)
                break

    def _add_item(self, chat):
        it = QListWidgetItem(self._format_text(chat))
        it.setData(Qt.UserRole, chat["id"])
        it.setSizeHint(QSize(240, 48))
        self.addItem(it)

    def _format_text(self, chat):
        status = chat.get("status", "")
        return f"{chat['title']}\n{chat['id']} • {status}"

    def _on_item_clicked(self, item):
        self.chat_selected.emit(item.data(Qt.UserRole))

    def _show_menu(self, pos):
        item = self.itemAt(pos)
        if not item:
            return
        chat_id = item.data(Qt.UserRole)
        menu = QMenu(self)
        rename = menu.addAction("Переименовать")
        delete = menu.addAction("Удалить")
        st_menu = menu.addMenu("Статус")
        for st in STATUS_CHOICES:
            st_menu.addAction(st)
        act = menu.exec_(self.mapToGlobal(pos))
        if not act:
            return
        if act == rename:
            self.chat_rename.emit(chat_id)
        elif act == delete:
            self.chat_delete.emit(chat_id)
        elif act.parentWidget() == st_menu:
            self.chat_change_status.emit(chat_id, act.text())
