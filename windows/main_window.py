from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout,
                               QWidget, QLabel, QPushButton, QTextEdit,
                               QScrollArea, QFrame, QLineEdit, QSplitter,
                               QListWidget, QListWidgetItem, QFileDialog,
                               QMessageBox, QStatusBar, QToolBar)
from PySide6.QtCore import Qt, QTimer, QDateTime, Signal
from PySide6.QtGui import QFont, QIcon, QAction, QPixmap
import json
from styles.theme_manager import theme_manager, ThemeType


class MessageBubble(QFrame):
    def __init__(self, message_data, is_user=True):
        super().__init__()
        self.message_data = message_data
        self.is_user = is_user
        self.setup_ui()
        self.apply_theme()

        # Подключаем обновление темы
        theme_manager.theme_changed.connect(self.apply_theme)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # Основной текст сообщения
        self.message_label = QLabel(self.message_data["text"])
        self.message_label.setWordWrap(True)
        self.message_label.setFont(QFont("Arial", 10))

        # Время и статус
        info_layout = QHBoxLayout()
        self.time_label = QLabel(self.message_data["time"])
        self.time_label.setFont(QFont("Arial", 8))

        info_layout.addWidget(self.time_label)

        if self.is_user:
            # Статус доставки для сообщений пользователя
            self.status_label = QLabel("✓✓" if self.message_data.get("delivered", True) else "✓")
            self.status_label.setFont(QFont("Arial", 8))
            info_layout.addWidget(self.status_label)
        else:
            # Имя оператора для сообщений поддержки
            self.operator_label = QLabel(self.message_data.get("operator", "Поддержка"))
            self.operator_label.setFont(QFont("Arial", 8))
            info_layout.addWidget(self.operator_label)

        layout.addWidget(self.message_label)
        layout.addLayout(info_layout)

    def apply_theme(self):
        """Применяем тему к пузырьку сообщения"""
        theme_data = theme_manager.get_theme_styles()
        colors = theme_data["colors"]

        if self.is_user:
            # Сообщения пользователя (справа, синие)
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["user_message"]};
                    border-radius: 12px;
                    color: white;
                    max-width: 300px;
                }}
            """)
            self.time_label.setStyleSheet(f"color: rgba(255, 255, 255, 0.7);")
            if hasattr(self, 'status_label'):
                self.status_label.setStyleSheet(f"color: rgba(255, 255, 255, 0.8);")
        else:
            # Сообщения поддержки (слева, серые)
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["operator_message"]};
                    border-radius: 12px;
                    color: {colors["text_primary"]};
                    max-width: 300px;
                    border: 1px solid {colors["border"]};
                }}
            """)
            self.time_label.setStyleSheet(f"color: {colors['text_muted']};")
            if hasattr(self, 'operator_label'):
                self.operator_label.setStyleSheet(f"color: {colors['success']}; font-weight: bold;")


class ChatArea(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.messages = []
        self.apply_theme()

        # Подключаем обновление темы
        theme_manager.theme_changed.connect(self.apply_theme)

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
        """Применяем тему к области чата"""
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

        # Создаем контейнер для выравнивания
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        if is_user:
            container_layout.addStretch()
            container_layout.addWidget(bubble)
        else:
            container_layout.addWidget(bubble)
            container_layout.addStretch()

        # Вставляем перед stretch
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, container)

        # Прокручиваем вниз
        QTimer.singleShot(100, self.scroll_to_bottom)

        self.messages.append(message_data)

    def scroll_to_bottom(self):
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


class MainWindow(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data

        # Инициализируем переменную toolbar
        self.main_toolbar = None

        # Подключаем обновление темы
        theme_manager.theme_changed.connect(self.apply_theme)

        self.setup_ui()
        self.setup_toolbar()
        self.setup_statusbar()
        self.apply_theme()  # Применяем тему после создания всех элементов
        self.load_sample_messages()

    def setup_ui(self):
        self.setWindowTitle(f"Чат поддержки - {self.user_data['name']}")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной макет
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Заголовок с информацией о пользователе
        self.header = self.create_header()
        main_layout.addWidget(self.header)

        # Разделитель
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter, 1)

        # Область чата
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        self.chat_area = ChatArea()
        chat_layout.addWidget(self.chat_area, 1)

        # Панель ввода
        self.input_panel = self.create_input_panel()
        chat_layout.addWidget(self.input_panel)

        # Боковая панель с информацией
        self.sidebar = self.create_sidebar()

        splitter.addWidget(chat_container)
        splitter.addWidget(self.sidebar)
        splitter.setSizes([600, 200])

    def create_header(self):
        header = QFrame()
        header.setFixedHeight(60)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)

        # Аватар пользователя
        self.avatar_label = QLabel(self.user_data["avatar"])
        self.avatar_label.setStyleSheet("font-size: 20px;")
        self.avatar_label.setFixedSize(40, 40)
        self.avatar_label.setAlignment(Qt.AlignCenter)

        # Информация о пользователе
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self.name_label = QLabel(self.user_data["name"])
        self.name_label.setFont(QFont("Arial", 12, QFont.Bold))

        self.details_label = QLabel(f"ID: {self.user_data['id']} • {self.user_data['status']}")
        self.details_label.setFont(QFont("Arial", 9))

        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.details_label)

        # Статус подключения
        self.connection_status = QLabel("🟢 Подключен")
        self.connection_status.setFont(QFont("Arial", 9))

        layout.addWidget(self.avatar_label)
        layout.addLayout(info_layout, 1)
        layout.addWidget(self.connection_status)

        return header

    def create_input_panel(self):
        panel = QFrame()
        panel.setFixedHeight(80)

        layout = QHBoxLayout(panel)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)

        # Поле ввода сообщения
        self.message_input = QTextEdit()
        self.message_input.setFixedHeight(50)
        self.message_input.setPlaceholderText("Введите ваше сообщение...")

        # Кнопки
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(5)

        # Кнопка прикрепить файл
        self.attach_btn = QPushButton("📎")
        self.attach_btn.setFixedSize(35, 25)
        self.attach_btn.setToolTip("Прикрепить файл")
        self.attach_btn.clicked.connect(self.attach_file)

        # Кнопка отправить
        self.send_btn = QPushButton("Отправить")
        self.send_btn.setFixedSize(80, 25)
        self.send_btn.clicked.connect(self.send_message)

        buttons_layout.addWidget(self.attach_btn)
        buttons_layout.addWidget(self.send_btn)

        layout.addWidget(self.message_input, 1)
        layout.addLayout(buttons_layout)

        # Отправка по Enter
        self.message_input.keyPressEvent = self.handle_key_press

        return panel

    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setMaximumWidth(250)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Заголовок боковой панели
        self.sidebar_title = QLabel("Информация")
        self.sidebar_title.setFont(QFont("Arial", 12, QFont.Bold))

        # Информация о пользователе
        self.user_info = QLabel(f"""
        <b>Контактные данные:</b><br>
        📧 {self.user_data['email']}<br>
        📱 {self.user_data['phone']}<br><br>
        <b>Статус:</b> {self.user_data['status']}<br>
        <b>ID:</b> {self.user_data['id']}
        """)
        self.user_info.setWordWrap(True)

        # Операторы онлайн
        self.operators_label = QLabel("Операторы онлайн:")
        self.operators_label.setFont(QFont("Arial", 10, QFont.Bold))

        self.operators_list = QListWidget()
        self.operators_list.setMaximumHeight(100)

        # Добавляем тестовых операторов
        self.operators_list.addItem("👩‍💼 Анна Петрова")
        self.operators_list.addItem("👨‍💻 Михаил Сидоров")
        self.operators_list.addItem("👩‍💻 Елена Козлова")

        # Кнопки действий
        self.actions_label = QLabel("Действия:")
        self.actions_label.setFont(QFont("Arial", 10, QFont.Bold))

        self.history_btn = QPushButton("📋 История чатов")
        self.settings_btn = QPushButton("⚙️ Настройки")
        self.logout_btn = QPushButton("🚪 Выход")

        self.logout_btn.clicked.connect(self.logout)

        layout.addWidget(self.sidebar_title)
        layout.addWidget(self.user_info)
        layout.addWidget(self.operators_label)
        layout.addWidget(self.operators_list)
        layout.addWidget(self.actions_label)
        layout.addWidget(self.history_btn)
        layout.addWidget(self.settings_btn)
        layout.addWidget(self.logout_btn)
        layout.addStretch()

        return sidebar

    def setup_toolbar(self):
        self.main_toolbar = QToolBar()
        self.addToolBar(self.main_toolbar)

        # Действия тулбара
        new_chat_action = QAction("🆕 Новый чат", self)
        history_action = QAction("📋 История", self)
        settings_action = QAction("⚙️ Настройки", self)

        # Добавляем переключение темы в тулбар
        theme_toggle_action = QAction("🌙/☀️ Тема", self)
        theme_toggle_action.setShortcut('Ctrl+T')
        theme_toggle_action.triggered.connect(theme_manager.toggle_theme)

        self.main_toolbar.addAction(new_chat_action)
        self.main_toolbar.addSeparator()
        self.main_toolbar.addAction(history_action)
        self.main_toolbar.addAction(settings_action)
        self.main_toolbar.addSeparator()
        self.main_toolbar.addAction(theme_toggle_action)

    def setup_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к отправке сообщений")

    def load_sample_messages(self):
        """Загружаем образцы сообщений для демонстрации"""
        sample_messages = [
            {"text": "Добро пожаловать в службу поддержки! Чем могу помочь?", "is_user": False,
             "operator": "Анна Петрова"},
            {"text": "Здравствуйте! У меня проблема с доступом к личному кабинету.", "is_user": True},
            {"text": "Понятно. Можете описать подробнее, какая именно ошибка появляется?", "is_user": False,
             "operator": "Анна Петрова"}
        ]

        for msg in sample_messages:
            self.chat_area.add_message(
                msg["text"],
                msg["is_user"],
                msg.get("operator")
            )

    def handle_key_press(self, event):
        """Обработка нажатий клавиш в поле ввода"""
        if event.key() == Qt.Key_Return and not event.modifiers() == Qt.ShiftModifier:
            self.send_message()
            event.accept()
        else:
            QTextEdit.keyPressEvent(self.message_input, event)

    def send_message(self):
        """Отправка сообщения"""
        text = self.message_input.toPlainText().strip()
        if not text:
            return

        # Добавляем сообщение пользователя
        self.chat_area.add_message(text, is_user=True)

        # Очищаем поле ввода
        self.message_input.clear()

        # Здесь будет отправка на сервер
        print(f"Отправлено сообщение: {text}")

        # Обновляем статус
        self.status_bar.showMessage(f"Сообщение отправлено в {QDateTime.currentDateTime().toString('hh:mm:ss')}")

        # Симулируем ответ оператора через 2 секунды
        QTimer.singleShot(2000, self.simulate_operator_response)

    def simulate_operator_response(self):
        """Симуляция ответа оператора"""
        responses = [
            "Спасибо за обращение! Сейчас разберемся с вашей проблемой.",
            "Передаю ваш запрос специалисту. Ожидайте ответа.",
            "Попробуйте выполнить следующие действия...",
            "Я вижу проблему. Исправляем."
        ]

        import random
        response = random.choice(responses)
        self.chat_area.add_message(response, is_user=False, operator="Анна Петрова")

    def attach_file(self):
        """Прикрепление файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл",
            "",
            "Все файлы (*.*)"
        )

        if file_path:
            file_name = file_path.split('/')[-1]
            self.chat_area.add_message(f"📎 Файл: {file_name}", is_user=True)
            print(f"Прикреплен файл: {file_path}")

    def logout(self):
        """Выход из системы"""
        reply = QMessageBox.question(
            self,
            'Подтверждение выхода',
            'Вы действительно хотите выйти из системы?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.close()
            # Здесь можно снова показать окно входа

    def apply_theme(self):
        """Применение текущей темы ко всем элементам"""
        theme_data = theme_manager.get_theme_styles()
        colors = theme_data["colors"]
        styles = theme_data["styles"]

        # Основное окно
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {colors["background"]};
                color: {colors["text_primary"]};
            }}
        """)

        # Заголовок
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

        # Панель ввода
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
                    font-size: 11px;
                    color: {colors["text_primary"]};
                }}
                QTextEdit:focus {{
                    border: 2px solid {colors["primary"]};
                }}
            """)

            # Стили кнопок
            button_style = f"""
                QPushButton {{
                    background-color: {colors["primary"]};
                    border: none;
                    border-radius: 4px;
                    color: white;
                    font-weight: bold;
                    font-size: 10px;
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

        # Боковая панель
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
                padding-bottom: 5px;
            """)

            self.user_info.setStyleSheet(f"color: {colors['text_secondary']}; font-size: 10px;")
            self.operators_label.setStyleSheet(f"color: {colors['text_primary']};")
            self.actions_label.setStyleSheet(f"color: {colors['text_primary']};")

            self.operators_list.setStyleSheet(f"""
                QListWidget {{
                    background-color: {colors["surface_alt"]};
                    border: 1px solid {colors["border"]};
                    border-radius: 4px;
                    font-size: 9px;
                    color: {colors["text_secondary"]};
                }}
                QListWidget::item {{
                    padding: 4px;
                    border-bottom: 1px solid {colors["border"]};
                }}
                QListWidget::item:hover {{
                    background-color: {colors["primary"]};
                    color: white;
                }}
            """)

            # Кнопки действий в сайдбаре
            sidebar_button_style = f"""
                QPushButton {{
                    background-color: {colors["surface_alt"]};
                    border: 1px solid {colors["border"]};
                    border-radius: 4px;
                    padding: 6px;
                    text-align: left;
                    font-size: 9px;
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

            for btn in [self.history_btn, self.settings_btn, self.logout_btn]:
                btn.setStyleSheet(sidebar_button_style)

        # Тулбар
        if hasattr(self, 'main_toolbar') and self.main_toolbar:
            self.main_toolbar.setStyleSheet(f"""
                QToolBar {{
                    background-color: {colors["surface_alt"]};
                    border-bottom: 1px solid {colors["border"]};
                    spacing: 5px;
                    padding: 5px;
                }}
                QToolBar QToolButton {{
                    color: {colors["text_primary"]};
                    font-size: 10px;
                    padding: 4px 8px;
                    border: none;
                    border-radius: 4px;
                }}
                QToolBar QToolButton:hover {{
                    background-color: {colors["primary"]};
                    color: white;
                }}
            """)

        # Статусбар
        if hasattr(self, 'status_bar'):
            self.status_bar.setStyleSheet(f"""
                QStatusBar {{
                    background-color: {colors["surface_alt"]};
                    color: {colors["text_secondary"]};
                    border-top: 1px solid {colors["border"]};
                    font-size: 9px;
                }}
            """)
