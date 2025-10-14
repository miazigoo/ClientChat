from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QCloseEvent
from styles.theme_manager import theme_manager
from integrations.backend_agent_api import BackendAgentAPI
from agent.agent_ids import AgentIDs

from .ui_manager import UIManager
from .chat_manager import ChatManager
from .realtime_handler import RealtimeHandler
from .theme_handler import ThemeHandler
from .message_handler import MessageHandler


class MainWindow(QMainWindow):
    """Главное окно чата поддержки"""

    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data

        # Инициализация базовых данных
        self._init_data()

        # Создание менеджеров
        self._create_managers()

        # Настройка приложения
        self._setup()

    def _init_data(self):
        """Инициализация базовых данных"""
        # Backend интеграция
        self.backend_api = BackendAgentAPI()
        self.backend_rooms = {}  # local_chat_id -> backend room_id
        self.room_to_local = {}  # backend room_id (str) -> local chat_id
        self._own_sent_ids = set()  # чтобы не дублировать свои сообщения из WS
        self.jwt_token = None
        self.ws_username = None

        # Состояние чатов пользователя
        self.chats = []  # список словарей чатов конкретного пользователя
        self.chats_by_id = {}  # индекс по id
        self.active_chat = None  # текущая заявка

        # Состояние UI
        self.left_chat = False
        self.main_toolbar = None

        # Агент данные
        self.agent_ids = AgentIDs(
            instance_id=str(self.user_data["id"]),  # временно fx_id, позже заменим на server instance_uid
            operator_id=str(self.user_data["name"])  # отображаемое ФИО
        )

    def _create_managers(self):
        """Создание менеджеров"""
        self.ui_manager = UIManager(self)
        self.chat_manager = ChatManager(self)
        self.realtime_handler = RealtimeHandler(self)
        self.theme_handler = ThemeHandler(self)
        self.message_handler = MessageHandler(self)

    def _setup(self):
        """Основная настройка окна"""
        # Подключение к менеджеру тем
        theme_manager.theme_changed.connect(self.theme_handler.apply_theme)

        # Настройка UI
        self.ui_manager.setup_ui()
        self.ui_manager.setup_toolbar()
        self.ui_manager.setup_statusbar()

        # Загрузка данных и инициализация
        self.chat_manager.load_user_chats()
        self.chat_manager.build_left_list()
        self.chat_manager.show_empty_state()

        # Инициализация real-time
        self.realtime_handler.init_realtime()

        # Настройка обработчиков сообщений
        self.message_handler.setup_message_input_handler()
        self.message_handler.connect_message_signals()

        # Применение темы
        self.theme_handler.apply_theme()

    # ========== Делегированные методы ==========
    # Методы чатов
    def create_new_chat(self):
        """Создание нового чата"""
        try:
            return self.chat_manager.create_new_chat()
        except Exception as e:
            print(f"Error creating chat: {e}")
            import traceback
            traceback.print_exc()
            self.status_bar.showMessage("Ошибка создания чата", 5000)

    def set_active_chat(self, chat_id):
        """Установка активного чата"""
        return self.chat_manager.set_active_chat(chat_id)

    def delete_chat(self, chat_id):
        """Удаление чата"""
        return self.chat_manager.delete_chat(chat_id)

    def rename_chat(self, chat_id=None):
        """Переименование чата"""
        return self.chat_manager.rename_chat(chat_id)

    def change_status(self, chat_id, status):
        """Изменение статуса чата"""
        return self.chat_manager.change_status(chat_id, status)

    def open_history(self):
        """Открытие истории чатов"""
        return self.chat_manager.open_history()

    def open_settings_placeholder(self):
        """Открытие настроек"""
        return self.chat_manager.open_settings()

    # Методы сообщений
    def send_message(self):
        """Отправка сообщения"""
        return self.message_handler.send_message()

    def attach_file(self):
        """Прикрепление файла"""
        return self.message_handler.attach_file()

    def on_files_dropped(self, paths):
        """Обработка drag&drop файлов"""
        return self.message_handler.on_files_dropped(paths)

    def logout(self):
        """Выход из системы"""
        return self.message_handler.logout()

    # Методы темы
    def apply_theme(self):
        """Применение темы"""
        return self.theme_handler.apply_theme()

    def update_header_for_chat(self):
        """Обновление заголовка для чата"""
        return self.theme_handler.update_header_for_chat()

    # Real-time методы
    def _subscribe_ws(self, chat_id: str):
        """Подписка на WS"""
        return self.realtime_handler.subscribe_ws(chat_id)

    def _ws_start_chat(self, chat_id: str):
        """Запуск WS чата"""
        return self.realtime_handler.ws_start_chat(chat_id)

    def _rt_send(self, text: str):
        """Отправка через RT"""
        return self.realtime_handler.rt_send(text)

    # Методы фильтрации
    def apply_chat_filters(self):
        """Применение фильтров чата"""
        return self.chat_manager.apply_chat_filters()

    def build_left_list(self):
        """Построение списка слева"""
        return self.chat_manager.build_left_list()

    def show_empty_state(self):
        """Показать пустое состояние"""
        return self.chat_manager.show_empty_state()

    # Слоты для обработки событий от реал-тайм обработчика
    @Slot()
    def _on_send_error(self):
        """Обработка ошибки отправки"""
        return self.realtime_handler.on_send_error()

    @Slot()
    def _on_leave_success_ui(self):
        """Успешное покидание чата"""
        return self.realtime_handler.on_leave_success_ui()

    @Slot()
    def _on_leave_error_ui(self):
        """Ошибка покидания чата"""
        return self.realtime_handler.on_leave_error_ui()

    def leave_chat(self):
        """Покинуть чат"""
        return self.realtime_handler.leave_chat()

    # ========== События окна ==========
    def closeEvent(self, event: QCloseEvent):
        """Обработка закрытия окна"""
        try:
            self.realtime_handler.close_connections()
        except Exception:
            pass
        super().closeEvent(event)

    # ========== Совместимость (методы которые могут вызываться извне) ==========
    def get_status_color(self, status):
        """Получение цвета статуса (для совместимости)"""
        return self.theme_handler.get_status_color(status)

    def handle_key_press(self, event):
        """Обработка клавиш (для совместимости)"""
        return self.message_handler.handle_key_press(event)

    # ========== Утилиты ==========
    def get_active_chat_id(self):
        """Получение ID активного чата"""
        return self.active_chat["id"] if self.active_chat else None

    def get_user_id(self):
        """Получение ID пользователя"""
        return self.user_data["id"]

    def is_chat_left(self):
        """Проверка - покинул ли пользователь чат"""
        return self.left_chat

    def get_chats_count(self):
        """Получение количества чатов"""
        return len(self.chats)

    def get_backend_room_id(self, chat_id):
        """Получение backend room ID по chat ID"""
        return self.backend_rooms.get(chat_id)

    @Slot()
    def _temp_update_room_mapping(self):
        """Временный слот для обновления маппинга комнат"""
        if hasattr(self, '_temp_update_room_mapping') and callable(self._temp_update_room_mapping):
            self._temp_update_room_mapping()
            # Удаляем временную функцию
            delattr(self, '_temp_update_room_mapping')
