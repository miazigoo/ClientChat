import os
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QSettings
from windows.login_window import LoginWindow
from styles.theme_manager import theme_manager, ThemeType
from realtime.server import ChatServer


class SupportChatApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle('Fusion')

        # Загружаем предпочтения пользователя (до применения темы)
        self.load_user_prefs()

        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

        # # Старт локального WebSocket-сервера (для демо real-time)
        # self.server = ChatServer()
        # self.server.start_in_background()

        # Окно входа
        self.login_window = LoginWindow()
        self.login_window.show()

        # Старт локального демо-сервера ТОЛЬКО если DEMO_WS=1
        if os.getenv("DEMO_WS", "0") == "1":
            from realtime.server import ChatServer
            self.server = ChatServer()
            self.server.start_in_background()

    def load_user_prefs(self):
        st = QSettings("SupportChat", "ClientApp")
        theme = st.value("theme", "dark")
        accent = st.value("accent", "blue")
        if accent == "custom":
            primary = st.value("custom_primary", "#0078d4")
            theme_manager.set_custom_accent(primary)
        else:
            theme_manager.set_accent(accent)
        theme_manager.set_theme(ThemeType.LIGHT if theme == "light" else ThemeType.DARK)

    def apply_theme(self):
        theme_data = theme_manager.get_theme_styles()
        app_style = theme_data["styles"]["main_window"]

        self.app.setStyleSheet(f"""
            QApplication {{
                background-color: {theme_data["colors"]["background"]};
                color: {theme_data["colors"]["text_primary"]};
            }}
            {app_style}
        """)

    def run(self):
        return self.app.exec()


if __name__ == "__main__":
    app = SupportChatApp()
    sys.exit(app.run())
