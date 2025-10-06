"""
Общие стили и константы для приложения
"""

def get_common_styles():
    """Возвращает общие стили, не зависящие от темы"""
    return {
        "fonts": {
            "primary": "Arial",
            "monospace": "Consolas, Monaco, monospace"
        },
        "sizes": {
            "border_radius": "6px",
            "small_border_radius": "4px",
            "large_border_radius": "12px"
        },
        "animations": {
            "transition": "all 0.2s ease-in-out"
        }
    }

def get_message_styles():
    """Стили для сообщений чата"""
    return {
        "max_width": "300px",
        "padding": "12px 16px",
        "margin": "4px 0",
        "font_size": "11px"
    }

def get_button_styles():
    """Базовые стили кнопок"""
    return {
        "padding": "8px 12px",
        "border_radius": "6px",
        "font_weight": "bold",
        "font_size": "10px",
        "min_height": "32px"
    }

def get_input_styles():
    """Стили для полей ввода"""
    return {
        "padding": "8px",
        "border_radius": "6px",
        "border_width": "2px",
        "font_size": "11px"
    }
