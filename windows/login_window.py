from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout,
                               QWidget, QLabel, QPushButton, QScrollArea,
                               QFrame, QLineEdit)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QAction
import os, json
from styles.theme_manager import theme_manager, ThemeType


class UserCard(QFrame):
    clicked = Signal(dict)

    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.setup_ui()
        self.apply_theme()

        # Подключаем обновление темы
        theme_manager.theme_changed.connect(self.apply_theme)

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)

        # Аватар
        self.avatar_label = QLabel(self.user_data["avatar"])
        self.avatar_label.setStyleSheet("font-size: 24px;")
        self.avatar_label.setFixedSize(40, 40)
        self.avatar_label.setAlignment(Qt.AlignCenter)

        # Информация о пользователе
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        # Имя
        self.name_label = QLabel(self.user_data["name"])
        self.name_label.setFont(QFont("Arial", 11, QFont.Bold))

        # ID и статус
        details_layout = QHBoxLayout()
        self.id_label = QLabel(f"ID: {self.user_data['id']}")
        self.id_label.setFont(QFont("Arial", 9))

        self.status_label = QLabel(self.user_data["status"])
        self.status_label.setFont(QFont("Arial", 9, QFont.Bold))

        details_layout.addWidget(self.id_label)
        details_layout.addStretch()
        details_layout.addWidget(self.status_label)

        info_layout.addWidget(self.name_label)
        info_layout.addLayout(details_layout)

        layout.addWidget(self.avatar_label)
        layout.addLayout(info_layout, 1)

        self.setCursor(Qt.PointingHandCursor)

    def get_status_color(self, theme_colors):
        """Получаем цвет статуса в зависимости от темы"""
        status = self.user_data["status"]
        if status == "VIP":
            return theme_colors["warning"]
        elif status == "Премиум":
            return theme_colors["error"]
        else:
            return theme_colors["success"]

    def apply_theme(self):
        """Применяем текущую тему"""
        theme_data = theme_manager.get_theme_styles()
        colors = theme_data["colors"]

        # Стили для карточки
        self.setStyleSheet(f"""
            UserCard {{
                background-color: {colors["surface_alt"]};
                border-radius: 8px;
                border: 1px solid {colors["border"]};
                margin: 2px;
            }}
            UserCard:hover {{
                background-color: {colors["surface"]};
                border: 1px solid {colors["primary"]};
            }}
        """)

        # Цвета текста
        self.name_label.setStyleSheet(f"color: {colors['text_primary']};")
        self.id_label.setStyleSheet(f"color: {colors['text_muted']};")
        self.status_label.setStyleSheet(f"color: {self.get_status_color(colors)};")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.user_data)


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.user_cards = []
        self.setup_menu()
        self.setup_ui()
        self.apply_theme()

        # Подключаем обновление темы
        theme_manager.theme_changed.connect(self.apply_theme)

    def setup_menu(self):
        """Создаем меню с настройками"""
        menubar = self.menuBar()

        # Меню "Вид"
        view_menu = menubar.addMenu('Вид')

        # Подменю "Тема"
        theme_menu = view_menu.addMenu('🎨 Тема')

        # Темная тема
        dark_theme_action = QAction('🌙 Темная', self)
        dark_theme_action.setCheckable(True)
        dark_theme_action.setChecked(theme_manager.get_current_theme() == ThemeType.DARK)
        dark_theme_action.triggered.connect(lambda: self.set_theme(ThemeType.DARK))

        # Светлая тема
        light_theme_action = QAction('☀️ Светлая', self)
        light_theme_action.setCheckable(True)
        light_theme_action.setChecked(theme_manager.get_current_theme() == ThemeType.LIGHT)
        light_theme_action.triggered.connect(lambda: self.set_theme(ThemeType.LIGHT))

        # Группируем действия (только одно может быть выбрано)
        from PySide6.QtGui import QActionGroup
        self.theme_group = QActionGroup(self)
        self.theme_group.addAction(dark_theme_action)
        self.theme_group.addAction(light_theme_action)

        theme_menu.addAction(dark_theme_action)
        theme_menu.addAction(light_theme_action)
        theme_menu.addSeparator()

        # Быстрое переключение
        toggle_theme_action = QAction('🔄 Переключить тему', self)
        toggle_theme_action.setShortcut('Ctrl+T')
        toggle_theme_action.triggered.connect(theme_manager.toggle_theme)
        theme_menu.addAction(toggle_theme_action)

        # Сохраняем ссылки на действия
        self.dark_theme_action = dark_theme_action
        self.light_theme_action = light_theme_action

        # Подменю "Акцент"
        accent_menu = view_menu.addMenu('🎨 Акцент')

        from PySide6.QtGui import QActionGroup
        self.accent_group = QActionGroup(self)

        def add_accent(label, key):
            act = QAction(label, self)
            act.setCheckable(True)
            act.setChecked(theme_manager.get_accent() == key)
            act.triggered.connect(lambda: theme_manager.set_accent(key))
            self.accent_group.addAction(act)
            accent_menu.addAction(act)

        add_accent('Синий', 'blue')
        add_accent('Зелёный', 'green')
        add_accent('Фиолетовый', 'purple')
        add_accent('Оранжевый', 'orange')

    def set_theme(self, theme_type: ThemeType):
        """Устанавливаем тему"""
        theme_manager.set_theme(theme_type)

        # Обновляем состояние действий меню
        self.dark_theme_action.setChecked(theme_type == ThemeType.DARK)
        self.light_theme_action.setChecked(theme_type == ThemeType.LIGHT)

    def setup_ui(self):
        self.setWindowTitle("Вход в систему поддержки")
        self.setFixedSize(450, 650)  # Увеличили высоту для меню

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 20, 30, 30)

        # Заголовок
        self.title_label = QLabel("Выберите пользователя")
        self.title_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)

        # Подзаголовок с информацией о теме
        self.theme_info_label = QLabel()
        self.theme_info_label.setFont(QFont("Arial", 9))
        self.theme_info_label.setAlignment(Qt.AlignCenter)
        self.update_theme_info()

        # Поиск
        search_layout = QVBoxLayout()
        self.search_label = QLabel("Поиск:")
        self.search_label.setFont(QFont("Arial", 10))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите имя или ID...")
        self.search_input.textChanged.connect(self.filter_users)

        search_layout.addWidget(self.search_label)
        search_layout.addWidget(self.search_input)

        # Список пользователей
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.users_widget = QWidget()
        self.users_layout = QVBoxLayout(self.users_widget)
        self.users_layout.setSpacing(5)
        self.users_layout.setContentsMargins(5, 5, 5, 5)

        self.scroll_area.setWidget(self.users_widget)

        # Создаем карточки пользователей
        self.create_user_cards()

        # Кнопка быстрого переключения темы
        theme_toggle_layout = QHBoxLayout()
        self.theme_toggle_btn = QPushButton("🌙/☀️ Сменить тему")
        self.theme_toggle_btn.setMaximumWidth(150)
        self.theme_toggle_btn.clicked.connect(theme_manager.toggle_theme)
        theme_toggle_layout.addStretch()
        theme_toggle_layout.addWidget(self.theme_toggle_btn)
        theme_toggle_layout.addStretch()

        layout.addWidget(self.title_label)
        layout.addWidget(self.theme_info_label)
        layout.addLayout(search_layout)
        layout.addWidget(self.scroll_area, 1)
        layout.addLayout(theme_toggle_layout)

    def create_user_cards(self):
        """Создаем карточки пользователей"""
        users = self._load_clients_from_json()
        for user in users:
            card = UserCard(user)
            card.clicked.connect(self.on_user_selected)
            self.user_cards.append(card)
            self.users_layout.addWidget(card)

        self.users_layout.addStretch()

    def _load_clients_from_json(self):
        base = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.normpath(os.path.join(base, "..", "agent", "agent_ids.json"))
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        users = []
        for key, val in data.items():
            fx_id = str(val.get("fx_id"))
            operator_id = str(val.get("operator_id"))
            operator_name = val.get("name", key)
            client_id = int(val.get("client_id", 0))
            users.append({
                "id": fx_id,                 # для UI показываем fx_id как ID
                "name": operator_name,       # отображаемое имя
                "email": f"{key.lower()}@example.com",
                "operator_id": operator_id,
                "client_id": client_id,
                "phone": "",
                "status": "Клиент",
                "avatar": "👤",
            })
        if not users:
            users = [{"id": "INST-LOCAL-DEV", "name": "Local Client", "email": "", "phone": "", "status": "Клиент",
                      "avatar": "👤"}]
        return users

    def filter_users(self, text):
        """Фильтрация пользователей по поисковому запросу"""
        for card in self.user_cards:
            user_data = card.user_data
            should_show = (
                    text.lower() in user_data["name"].lower() or
                    text.lower() in user_data["id"].lower()
            )
            card.setVisible(should_show)

    def on_user_selected(self, user_data):
        """Обработка выбора пользователя"""
        print(f"Выбран пользователь: {user_data['name']} (ID: {user_data['id']})")

        # Импортируем здесь чтобы избежать циклического импорта
        from windows.main_window import MainWindow

        # Открываем главное окно
        self.main_window = MainWindow(user_data)
        self.main_window.show()

        # Закрываем окно входа
        self.close()

    def update_theme_info(self):
        """Обновляем информацию о текущей теме"""
        theme_data = theme_manager.get_theme_styles()
        theme_name = theme_data["name"]
        shortcut_hint = "Ctrl+T для быстрого переключения"
        self.theme_info_label.setText(f"Текущая тема: {theme_name} • {shortcut_hint}")

    def apply_theme(self):
        """Применяем текущую тему"""
        theme_data = theme_manager.get_theme_styles()
        colors = theme_data["colors"]
        styles = theme_data["styles"]

        # Обновляем информацию о теме
        self.update_theme_info()

        # Основные стили окна
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {colors["background"]};
                color: {colors["text_primary"]};
            }}
            QMenuBar {{
                background-color: {colors["surface"]};
                color: {colors["text_primary"]};
                border-bottom: 1px solid {colors["border"]};
                padding: 2px;
            }}
            QMenuBar::item {{
                background-color: transparent;
                padding: 4px 8px;
                border-radius: 4px;
            }}
            QMenuBar::item:selected {{
                background-color: {colors["primary"]};
                color: white;
            }}
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
            QMenu::item:checked {{
                background-color: {colors["surface_alt"]};
                color: {colors["primary"]};
                font-weight: bold;
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {colors["border"]};
                margin: 4px 0;
            }}
        """)

        # Стили для элементов UI
        if hasattr(self, 'title_label'):
            self.title_label.setStyleSheet(f"color: {colors['text_primary']};")

        if hasattr(self, 'theme_info_label'):
            self.theme_info_label.setStyleSheet(f"color: {colors['text_muted']};")

        if hasattr(self, 'search_label'):
            self.search_label.setStyleSheet(f"color: {colors['text_secondary']};")

        if hasattr(self, 'search_input'):
            self.search_input.setStyleSheet(styles["input"])

        if hasattr(self, 'scroll_area'):
            self.scroll_area.setStyleSheet(f"""
                {styles["scroll_area"]}
                QScrollArea {{
                    border: 1px solid {colors["border"]};
                    border-radius: 8px;
                    background-color: {colors["surface"]};
                }}
            """)

        if hasattr(self, 'theme_toggle_btn'):
            self.theme_toggle_btn.setStyleSheet(f"""
                {styles["button"]}
                QPushButton {{
                    background-color: {colors["surface_alt"]};
                    color: {colors["text_primary"]};
                    border: 1px solid {colors["border"]};
                }}
                QPushButton:hover {{
                    background-color: {colors["primary"]};
                    color: white;
                }}
            """)
