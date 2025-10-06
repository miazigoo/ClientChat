import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from windows.login_window import LoginWindow
from styles.theme_manager import theme_manager, ThemeType


class SupportChatApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle('Fusion')  # Современный стиль

        # Инициализируем тему
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

        # Запускаем окно входа
        self.login_window = LoginWindow()
        self.login_window.show()

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
