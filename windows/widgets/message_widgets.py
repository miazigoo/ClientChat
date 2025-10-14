import os
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QFont, QPixmap, QDesktopServices
from styles.theme_manager import theme_manager


class MessageBubble(QFrame):
    def __init__(self, message_data, is_user=True):
        super().__init__()
        self.message_data = message_data
        self.is_user = is_user
        self.setup_ui()
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

    def __del__(self):
        # Отключаем сигналы при удалении
        try:
            theme_manager.theme_changed.disconnect(self.apply_theme)
        except:
            pass

    def deleteLater(self):
        # Отключаем сигналы перед удалением
        try:
            theme_manager.theme_changed.disconnect(self.apply_theme)
        except:
            pass
        super().deleteLater()

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
