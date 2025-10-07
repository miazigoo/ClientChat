from PySide6.QtCore import QObject, Signal
from enum import Enum


class ThemeType(Enum):
    DARK = "dark"
    LIGHT = "light"


class ThemeManager(QObject):
    theme_changed = Signal(str)  # Сигнал об изменении темы

    def __init__(self):
        super().__init__()
        self._accent = "blue"
        self._ACCENTS = {
            "blue": {"primary": "#0078d4", "hover": "#106ebe", "pressed": "#005a9e"},
            "green": {"primary": "#2e8b57", "hover": "#247a4f", "pressed": "#1e6a43"},
            "purple": {"primary": "#7e57c2", "hover": "#6a4eb2", "pressed": "#5b3ea2"},
            "orange": {"primary": "#ff8c00", "hover": "#ff7a00", "pressed": "#e06d00"},
        }
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
        acc = self._ACCENTS[self._accent]
        return {
            "name": "Темная",
            "colors": {
                "primary": acc["primary"],
                "primary_hover": acc["hover"],
                "primary_pressed": acc["pressed"],
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
                "user_message": acc["primary"],
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
                "button": f"""
                   QPushButton {{
                       background-color: {acc["primary"]};
                       border: none;
                       border-radius: 6px;
                       color: white;
                       font-weight: bold;
                       font-size: 10px;
                       padding: 8px 12px;
                   }}
                   QPushButton:hover {{
                       background-color: {acc["hover"]};
                   }}
                   QPushButton:pressed {{
                       background-color: {acc["pressed"]};
                   }}
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
        acc = self._ACCENTS[self._accent]
        return {
            "name": "Светлая",
            "colors": {
                "primary": acc["primary"],
                "primary_hover": acc["hover"],
                "primary_pressed": acc["pressed"],
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
                "user_message": acc["primary"],
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
                "button": f"""
                   QPushButton {{
                       background-color: {acc["primary"]};
                       border: none;
                       border-radius: 6px;
                       color: white;
                       font-weight: bold;
                       font-size: 10px;
                       padding: 8px 12px;
                   }}
                   QPushButton:hover {{
                       background-color: {acc["hover"]};
                   }}
                   QPushButton:pressed {{
                       background-color: {acc["pressed"]};
                   }}
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

    def get_accent(self):
        return self._accent

    def set_accent(self, accent_name: str):
        if accent_name not in self._ACCENTS:
            return
        if accent_name == self._accent:
            return
        self._accent = accent_name
        # Пересобираем темы с новым акцентом и оповестим
        self._themes = {
            ThemeType.DARK: self._get_dark_theme(),
            ThemeType.LIGHT: self._get_light_theme()
        }
        self.theme_changed.emit(self._current_theme.value)

    def _hex_to_rgb(self, hx):
        hx = hx.lstrip('#')
        return tuple(int(hx[i:i+2], 16) for i in (0, 2, 4))

    def _rgb_to_hex(self, rgb):
        return "#{:02x}{:02x}{:02x}".format(*rgb)

    def _mix(self, rgb, factor):  # factor в диапазоне [-1..1], <0 темнее, >0 светлее
        if factor < 0:
            k = 1 + factor
            return tuple(max(0, int(c * k)) for c in rgb)
        else:
            return tuple(min(255, int(c + (255 - c) * factor)) for c in rgb)

    def set_custom_accent(self, primary_hex: str):
        try:
            base = self._hex_to_rgb(primary_hex)
        except Exception:
            return
        hover = self._rgb_to_hex(self._mix(base, -0.12))
        pressed = self._rgb_to_hex(self._mix(base, -0.22))
        self._ACCENTS["custom"] = {
            "primary": primary_hex,
            "hover": hover,
            "pressed": pressed,
        }
        self.set_accent("custom")



# Глобальный экземпляр менеджера тем
theme_manager = ThemeManager()
