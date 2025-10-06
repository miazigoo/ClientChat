from PySide6.QtCore import QObject, Signal
from enum import Enum


class ThemeType(Enum):
    DARK = "dark"
    LIGHT = "light"


class ThemeManager(QObject):
    theme_changed = Signal(str)  # Сигнал об изменении темы

    def __init__(self):
        super().__init__()
        self._current_theme = ThemeType.DARK
        self._themes = {
            ThemeType.DARK: self._get_dark_theme(),
            ThemeType.LIGHT: self._get_light_theme()
        }

    def get_current_theme(self):
        return self._current_theme

    def set_theme(self, theme_type: ThemeType):
        if theme_type != self._current_theme:
            self._current_theme = theme_type
            self.theme_changed.emit(theme_type.value)

    def toggle_theme(self):
        new_theme = ThemeType.LIGHT if self._current_theme == ThemeType.DARK else ThemeType.DARK
        self.set_theme(new_theme)

    def get_theme_styles(self, theme_type: ThemeType = None):
        if theme_type is None:
            theme_type = self._current_theme
        return self._themes[theme_type]

    def _get_dark_theme(self):
        return {
            "name": "Темная",
            "colors": {
                "primary": "#0078d4",
                "primary_hover": "#106ebe",
                "primary_pressed": "#005a9e",
                "background": "#2b2b2b",
                "surface": "#333333",
                "surface_alt": "#3c3c3c",
                "border": "#555555",
                "text_primary": "#ffffff",
                "text_secondary": "#cccccc",
                "text_muted": "#888888",
                "success": "#4ECDC4",
                "warning": "#FFD700",
                "error": "#FF6B6B",
                "user_message": "#0078d4",
                "operator_message": "#3c3c3c",
                "online": "#4ECDC4"
            },
            "styles": {
                "main_window": """
                    QMainWindow {
                        background-color: #2b2b2b;
                        color: #ffffff;
                    }
                """,
                "button": """
                    QPushButton {
                        background-color: #0078d4;
                        border: none;
                        border-radius: 6px;
                        color: white;
                        font-weight: bold;
                        font-size: 10px;
                        padding: 8px 12px;
                    }
                    QPushButton:hover {
                        background-color: #106ebe;
                    }
                    QPushButton:pressed {
                        background-color: #005a9e;
                    }
                """,
                "input": """
                    QLineEdit, QTextEdit {
                        background-color: #3c3c3c;
                        border: 2px solid #555555;
                        border-radius: 6px;
                        padding: 8px;
                        font-size: 11px;
                        color: #ffffff;
                    }
                    QLineEdit:focus, QTextEdit:focus {
                        border: 2px solid #0078d4;
                    }
                """,
                "scroll_area": """
                    QScrollArea {
                        border: none;
                        background-color: #2b2b2b;
                    }
                    QScrollBar:vertical {
                        background-color: #3c3c3c;
                        width: 8px;
                        border-radius: 4px;
                    }
                    QScrollBar::handle:vertical {
                        background-color: #555555;
                        border-radius: 4px;
                        min-height: 20px;
                    }
                    QScrollBar::handle:vertical:hover {
                        background-color: #777777;
                    }
                """
            }
        }

    def _get_light_theme(self):
        return {
            "name": "Светлая",
            "colors": {
                "primary": "#0078d4",
                "primary_hover": "#106ebe",
                "primary_pressed": "#005a9e",
                "background": "#ffffff",
                "surface": "#f5f5f5",
                "surface_alt": "#e8e8e8",
                "border": "#d0d0d0",
                "text_primary": "#000000",
                "text_secondary": "#333333",
                "text_muted": "#666666",
                "success": "#008080",
                "warning": "#ff8c00",
                "error": "#dc3545",
                "user_message": "#0078d4",
                "operator_message": "#f0f0f0",
                "online": "#008080"
            },
            "styles": {
                "main_window": """
                    QMainWindow {
                        background-color: #ffffff;
                        color: #000000;
                    }
                """,
                "button": """
                    QPushButton {
                        background-color: #0078d4;
                        border: none;
                        border-radius: 6px;
                        color: white;
                        font-weight: bold;
                        font-size: 10px;
                        padding: 8px 12px;
                    }
                    QPushButton:hover {
                        background-color: #106ebe;
                    }
                    QPushButton:pressed {
                        background-color: #005a9e;
                    }
                """,
                "input": """
                    QLineEdit, QTextEdit {
                        background-color: #ffffff;
                        border: 2px solid #d0d0d0;
                        border-radius: 6px;
                        padding: 8px;
                        font-size: 11px;
                        color: #000000;
                    }
                    QLineEdit:focus, QTextEdit:focus {
                        border: 2px solid #0078d4;
                    }
                """,
                "scroll_area": """
                    QScrollArea {
                        border: none;
                        background-color: #ffffff;
                    }
                    QScrollBar:vertical {
                        background-color: #f0f0f0;
                        width: 8px;
                        border-radius: 4px;
                    }
                    QScrollBar::handle:vertical {
                        background-color: #c0c0c0;
                        border-radius: 4px;
                        min-height: 20px;
                    }
                    QScrollBar::handle:vertical:hover {
                        background-color: #a0a0a0;
                    }
                """
            }
        }


# Глобальный экземпляр менеджера тем
theme_manager = ThemeManager()
