from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame,
                               QLabel, QPushButton, QTextEdit, QSplitter,
                               QStackedWidget, QLineEdit, QComboBox, QListWidget,
                               QToolBar, QStatusBar)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QAction
from windows.widgets.chat_list import ChatList
from windows.widgets.chat_area import ChatArea

STATUS_CHOICES = ("Новая", "В работе", "Ожидает клиента", "Ожидает оператора", "Закрыта")


class UIManager:
    """Менеджер создания UI элементов"""

    def __init__(self, main_window):
        self.main_window = main_window

    def setup_ui(self):
        """Основная настройка интерфейса"""
        mw = self.main_window
        mw.setWindowTitle(f"Чат поддержки - {mw.user_data['name']}")
        mw.setGeometry(100, 100, 900, 640)

        central_widget = QWidget()
        mw.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Заголовок
        mw.header = self.create_header()
        main_layout.addWidget(mw.header)

        # Основной сплиттер
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter, 1)

        # LEFT: панель со списком, поиском и массовыми действиями
        mw.left_panel = self.create_left_panel()

        # CENTER: стек (пустое состояние / чат)
        mw.center_stack = QStackedWidget()

        # Пустое состояние
        mw.empty_state = self.create_empty_state()
        mw.center_stack.addWidget(mw.empty_state)

        # Страница чата
        mw.chat_page = QWidget()
        chat_layout = QVBoxLayout(mw.chat_page)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        mw.chat_area = ChatArea()
        chat_layout.addWidget(mw.chat_area, 1)

        mw.input_panel = self.create_input_panel()
        chat_layout.addWidget(mw.input_panel)
        mw.center_stack.addWidget(mw.chat_page)

        # RIGHT: боковая панель
        mw.sidebar = self.create_sidebar()

        splitter.addWidget(mw.left_panel)
        splitter.addWidget(mw.center_stack)
        splitter.addWidget(mw.sidebar)
        splitter.setSizes([280, 580, 240])

        # Константы индексов стека
        mw.CENTER_EMPTY = 0
        mw.CENTER_CHAT = 1

    def create_header(self):
        """Создание заголовка"""
        mw = self.main_window

        header = QFrame()
        header.setFixedHeight(68)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(14)

        # Аватар пользователя
        mw.avatar_label = QLabel(mw.user_data["avatar"])
        mw.avatar_label.setStyleSheet("font-size: 22px;")
        mw.avatar_label.setFixedSize(44, 44)
        mw.avatar_label.setAlignment(Qt.AlignCenter)

        # Информация о пользователе
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        mw.name_label = QLabel(mw.user_data["name"])
        mw.name_label.setFont(QFont("Arial", 12, QFont.Bold))

        # Блок с ID пользователя + текущая заявка (ID + статус)
        sub_layout = QHBoxLayout()
        sub_layout.setSpacing(8)

        mw.details_label = QLabel(f"ID: {mw.user_data['id']} • {mw.user_data['status']}")
        mw.details_label.setFont(QFont("Arial", 9))

        mw.ticket_label = QLabel("")  # CH-XXXX
        mw.ticket_label.setFont(QFont("Arial", 9, QFont.Bold))

        mw.ticket_status_label = QLabel("")  # Чип статуса
        mw.ticket_status_label.setFont(QFont("Arial", 9, QFont.Bold))
        mw.ticket_status_label.setContentsMargins(8, 2, 8, 2)

        mw.operator_count_label = QLabel("")  # «Операторов: N»
        mw.operator_count_label.setFont(QFont("Arial", 9))
        mw.operator_count_label.setContentsMargins(8, 2, 8, 2)

        sub_layout.addWidget(mw.details_label)
        sub_layout.addSpacing(10)
        sub_layout.addWidget(mw.ticket_label)
        sub_layout.addWidget(mw.ticket_status_label)
        sub_layout.addWidget(mw.operator_count_label)
        sub_layout.addStretch()

        info_layout.addWidget(mw.name_label)
        info_layout.addLayout(sub_layout)

        # Статус подключения
        mw.connection_status = QLabel("🟢 Подключен")
        mw.connection_status.setFont(QFont("Arial", 10))

        layout.addWidget(mw.avatar_label)
        layout.addLayout(info_layout, 1)
        layout.addWidget(mw.connection_status)

        return header

    def create_left_panel(self):
        """Создание левой панели"""
        mw = self.main_window

        panel = QFrame()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(8)

        # Поиск
        mw.search_input = QLineEdit()
        mw.search_input.setPlaceholderText("Поиск по названию или ID...")

        # Фильтр статуса
        mw.status_filter = QComboBox()
        mw.status_filter.addItem("Все статусы")
        for st in STATUS_CHOICES:
            mw.status_filter.addItem(st)

        # Массовые действия
        mw.bulk_close_btn = QPushButton("✔ Закрыть выбранные")
        mw.bulk_delete_btn = QPushButton("🗑 Удалить выбранные")

        # Список чатов
        mw.chat_list = ChatList()

        lay.addWidget(mw.search_input)
        lay.addWidget(mw.status_filter)
        lay.addWidget(mw.bulk_close_btn)
        lay.addWidget(mw.bulk_delete_btn)
        lay.addWidget(mw.chat_list, 1)

        return panel

    def create_input_panel(self):
        """Создание панели ввода"""
        mw = self.main_window

        panel = QFrame()
        panel.setFixedHeight(84)

        layout = QHBoxLayout(panel)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)

        # Поле ввода сообщения
        mw.message_input = QTextEdit()
        mw.message_input.setFixedHeight(56)
        mw.message_input.setPlaceholderText("Введите ваше сообщение...")

        mw.message_input.destroyed.connect(lambda: print("MessageInput destroyed"))

        # Кнопки
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(6)

        mw.attach_btn = QPushButton("📎")
        mw.attach_btn.setFixedSize(38, 26)
        mw.attach_btn.setToolTip("Прикрепить файл")

        mw.send_btn = QPushButton("Отправить")
        mw.send_btn.setFixedSize(92, 26)

        buttons_layout.addWidget(mw.attach_btn)
        buttons_layout.addWidget(mw.send_btn)

        layout.addWidget(mw.message_input, 1)
        layout.addLayout(buttons_layout)

        return panel

    def create_empty_state(self):
        """Создание пустого состояния"""
        mw = self.main_window

        panel = QFrame()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addStretch()

        title = QLabel("Нет активного диалога")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Выберите диалог слева или создайте новую заявку")
        subtitle.setAlignment(Qt.AlignCenter)

        btn = QPushButton("🆕 Создать заявку")
        btn.setFixedSize(220, 44)

        lay.addWidget(title)
        lay.addWidget(subtitle)

        hl = QHBoxLayout()
        hl.addStretch()
        hl.addWidget(btn)
        hl.addStretch()
        lay.addLayout(hl)
        lay.addStretch()

        # Сохраняем ссылку на кнопку для подключения сигналов
        mw.empty_create_btn = btn

        return panel

    def create_sidebar(self):
        """Создание боковой панели"""
        mw = self.main_window

        sidebar = QFrame()
        sidebar.setMaximumWidth(270)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(16)

        # Заголовок боковой панели
        mw.sidebar_title = QLabel("Информация")
        mw.sidebar_title.setFont(QFont("Arial", 13, QFont.Bold))

        # Информация о пользователе
        mw.user_info = QLabel(f"""
        <b>Контактные данные:</b><br>
        📧 {mw.user_data['email']}<br>
        📱 {mw.user_data['phone']}<br><br>
        <b>Статус:</b> {mw.user_data['status']}<br>
        <b>ID:</b> {mw.user_data['id']}
        """)
        mw.user_info.setWordWrap(True)

        # Операторы онлайн
        mw.operators_label = QLabel("Операторы онлайн:")
        mw.operators_label.setFont(QFont("Arial", 11, QFont.Bold))

        mw.operators_list = QListWidget()
        mw.operators_list.setMaximumHeight(120)
        mw.operators_list.addItem("👩‍💼 Петрова Аня")
        mw.operators_list.addItem("👨‍💻 Сидоров Михаил")
        mw.operators_list.addItem("👩‍💻 Головач Лена")

        # Действия
        mw.actions_label = QLabel("Действия:")
        mw.actions_label.setFont(QFont("Arial", 11, QFont.Bold))

        # Кнопки действий
        mw.new_chat_btn = QPushButton("🆕 Новый чат")
        mw.history_btn = QPushButton("📋 История чатов")
        mw.settings_btn = QPushButton("⚙️ Настройки")
        mw.leave_chat_btn = QPushButton("⛔ Покинуть чат")
        mw.logout_btn = QPushButton("🚪 Выход")

        layout.addWidget(mw.sidebar_title)
        layout.addWidget(mw.user_info)
        layout.addWidget(mw.operators_label)
        layout.addWidget(mw.operators_list)
        layout.addWidget(mw.actions_label)
        layout.addWidget(mw.new_chat_btn)
        layout.addWidget(mw.history_btn)
        layout.addWidget(mw.settings_btn)
        layout.addWidget(mw.leave_chat_btn)
        layout.addWidget(mw.logout_btn)
        layout.addStretch()

        return sidebar

    def setup_toolbar(self):
        """Настройка тулбара"""
        mw = self.main_window

        mw.main_toolbar = QToolBar()
        mw.addToolBar(mw.main_toolbar)

        # Действия тулбара
        new_chat_action = QAction("🆕 Новый чат", mw)
        rename_action = QAction("✏️ Переименовать", mw)
        settings_action = QAction("⚙️ Настройки", mw)

        theme_toggle_action = QAction("🌙/☀️ Тема", mw)
        theme_toggle_action.setShortcut('Ctrl+T')

        mw.main_toolbar.addAction(new_chat_action)
        mw.main_toolbar.addSeparator()
        mw.main_toolbar.addAction(rename_action)
        mw.main_toolbar.addAction(settings_action)
        mw.main_toolbar.addSeparator()
        mw.main_toolbar.addAction(theme_toggle_action)

        # Сохраняем действия для подключения сигналов
        mw.toolbar_actions = {
            'new_chat': new_chat_action,
            'rename': rename_action,
            'settings': settings_action,
            'theme_toggle': theme_toggle_action
        }

    def setup_statusbar(self):
        """Настройка статусбара"""
        mw = self.main_window

        mw.status_bar = QStatusBar()
        mw.setStatusBar(mw.status_bar)
        mw.status_bar.showMessage("Готов к отправке сообщений")
