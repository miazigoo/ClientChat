"""
Модуль главного окна чата поддержки.

Этот модуль содержит все компоненты, необходимые для работы
главного окна приложения чата поддержки.

Основные компоненты:
- MainWindow: Главный класс окна
- UIManager: Менеджер пользовательского интерфейса
- ChatManager: Менеджер работы с чатами
- RealtimeHandler: Обработчик real-time соединений
- ThemeHandler: Обработчик тем и стилей
- MessageHandler: Обработчик сообщений и файлов
"""

from .main_window import MainWindow
from .ui_manager import UIManager
from .chat_manager import ChatManager
from .realtime_handler import RealtimeHandler
from .theme_handler import ThemeHandler
from .message_handler import MessageHandler

__version__ = "1.0.0"
__author__ = "Support Chat Team"

# Основной экспорт для обратной совместимости
__all__ = [
    "MainWindow",
    "UIManager",
    "ChatManager",
    "RealtimeHandler",
    "ThemeHandler",
    "MessageHandler"
]

# Константы модуля
DEFAULT_CHAT_TITLE = "Новая заявка"
MAX_MESSAGE_LENGTH = 5000
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Статусы чатов
CHAT_STATUSES = (
    "Новая",
    "В работе",
    "Ожидает клиента",
    "Ожидает оператора",
    "Закрыта"
)

# Поддерживаемые расширения файлов
SUPPORTED_FILE_EXTENSIONS = {
    'images': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'],
    'documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
    'archives': ['.zip', '.rar', '.7z'],
    'spreadsheets': ['.csv', '.xlsx', '.xls'],
    'presentations': ['.ppt', '.pptx']
}

def get_version():
    """Возвращает версию модуля"""
    return __version__

def get_all_supported_extensions():
    """Возвращает все поддерживаемые расширения файлов"""
    extensions = []
    for ext_list in SUPPORTED_FILE_EXTENSIONS.values():
        extensions.extend(ext_list)
    return extensions

def is_image_file(filename):
    """Проверяет, является ли файл изображением"""
    import os
    ext = os.path.splitext(filename.lower())[1]
    return ext in SUPPORTED_FILE_EXTENSIONS['images']

def format_file_size(size_bytes):
    """Форматирует размер файла в человекочитаемый формат"""
    for unit in ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ']:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} ПБ"

# Конфигурация по умолчанию
DEFAULT_CONFIG = {
    'window_geometry': (100, 100, 900, 640),
    'splitter_sizes': [280, 580, 240],
    'header_height': 68,
    'input_panel_height': 84,
    'sidebar_max_width': 270,
    'operators_list_height': 120,
    'chat_bubble_max_width': 360,
    'image_preview_max_width': 320
}

def get_default_config():
    """Возвращает конфигурацию по умолчанию"""
    return DEFAULT_CONFIG.copy()
