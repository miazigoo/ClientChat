from styles.theme_manager import theme_manager


class ThemeHandler:
    """Обработчик тем и стилей"""

    def __init__(self, main_window):
        self.main_window = main_window

    def apply_theme(self):
        """Применение текущей темы"""
        mw = self.main_window

        if hasattr(mw, 'empty_state'):
            # никаких спец. стилей — наследуется
            pass

        theme_data = theme_manager.get_theme_styles()
        colors = theme_data["colors"]
        styles = theme_data["styles"]

        # Основные стили окна
        mw.setStyleSheet(f"""
            QMainWindow {{
                background-color: {colors["background"]};
                color: {colors["text_primary"]};
            }}
        """)

        # Применяем стили к основным компонентам
        self._apply_header_theme(colors)
        self._apply_input_panel_theme(colors, styles)
        self._apply_sidebar_theme(colors)
        self._apply_toolbar_theme(colors)
        self._apply_statusbar_theme(colors)
        self._apply_left_panel_theme(colors, styles)

    def _apply_header_theme(self, colors):
        """Применение темы к заголовку"""
        mw = self.main_window

        if not hasattr(mw, 'header'):
            return

        mw.header.setStyleSheet(f"""
            QFrame {{
                background-color: {colors["surface"]};
                border-bottom: 1px solid {colors["border"]};
            }}
        """)

        mw.name_label.setStyleSheet(f"color: {colors['text_primary']};")
        mw.details_label.setStyleSheet(f"color: {colors['text_muted']};")
        mw.connection_status.setStyleSheet(f"color: {colors['success']};")

        if mw.left_chat:
            mw.connection_status.setStyleSheet(f"color: {colors['error']};")
            mw.connection_status.setText("⛔ Вы покинули чат")

        # Чип статуса и тикет
        if mw.active_chat:
            st_color = self.get_status_color(mw.active_chat["status"])
        else:
            st_color = colors["text_muted"]

        mw.ticket_label.setStyleSheet(f"color: {colors['text_secondary']};")
        mw.ticket_status_label.setStyleSheet(f"""
            color: white;
            background-color: {st_color};
            border-radius: 10px;
            padding: 2px 8px;
        """)

        if hasattr(mw, 'operator_count_label'):
            mw.operator_count_label.setStyleSheet(f"color: {colors['text_secondary']};")

    def _apply_input_panel_theme(self, colors, styles):
        """Применение темы к панели ввода"""
        mw = self.main_window

        if not hasattr(mw, 'input_panel'):
            return

        mw.input_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {colors["surface"]};
                border-top: 1px solid {colors["border"]};
            }}
        """)

        mw.message_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {colors["surface_alt"]};
                border: 2px solid {colors["border"]};
                border-radius: 8px;
                padding: 8px;
                font-size: 12px;
                color: {colors["text_primary"]};
            }}
            QTextEdit:focus {{
                border: 2px solid {colors["primary"]};
            }}
        """)

        button_style = f"""
            QPushButton {{
                background-color: {colors["primary"]};
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: bold;
                font-size: 11px;
                padding: 6px 10px;
            }}
            QPushButton:hover {{
                background-color: {colors["primary_hover"]};
            }}
            QPushButton:pressed {{
                background-color: {colors["primary_pressed"]};
            }}
            QPushButton:disabled {{
                background-color: {colors["text_muted"]};
                color: {colors["surface_alt"]};
            }}
        """

        mw.send_btn.setStyleSheet(button_style)
        mw.attach_btn.setStyleSheet(button_style)

    def _apply_sidebar_theme(self, colors):
        """Применение темы к боковой панели"""
        mw = self.main_window

        if not hasattr(mw, 'sidebar'):
            return

        mw.sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {colors["surface"]};
                border-left: 1px solid {colors["border"]};
            }}
        """)

        mw.sidebar_title.setStyleSheet(f"""
            color: {colors['text_primary']}; 
            border-bottom: 1px solid {colors['border']}; 
            padding-bottom: 6px;
        """)

        # Увеличили шрифты правого меню
        mw.user_info.setStyleSheet(f"color: {colors['text_secondary']}; font-size: 12px;")
        mw.operators_label.setStyleSheet(f"color: {colors['text_primary']};")
        mw.actions_label.setStyleSheet(f"color: {colors['text_primary']};")

        mw.operators_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {colors["surface_alt"]};
                border: 1px solid {colors["border"]};
                border-radius: 6px;
                font-size: 11px;
                color: {colors["text_secondary"]};
            }}
            QListWidget::item {{
                padding: 6px;
                border-bottom: 1px solid {colors["border"]};
            }}
            QListWidget::item:hover {{
                background-color: {colors["primary"]};
                color: white;
            }}
        """)

        sidebar_button_style = f"""
            QPushButton {{
                background-color: {colors["surface_alt"]};
                border: 1px solid {colors["border"]};
                border-radius: 6px;
                padding: 8px;
                text-align: left;
                font-size: 11px;
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

        for btn in [mw.history_btn, mw.settings_btn, mw.logout_btn, mw.new_chat_btn]:
            btn.setStyleSheet(sidebar_button_style)
        mw.leave_chat_btn.setStyleSheet(sidebar_button_style)

    def _apply_toolbar_theme(self, colors):
        """Применение темы к тулбару"""
        mw = self.main_window

        if not hasattr(mw, 'main_toolbar') or not mw.main_toolbar:
            return

        mw.main_toolbar.setStyleSheet(f"""
            QToolBar {{
                background-color: {colors["surface_alt"]};
                border-bottom: 1px solid {colors["border"]};
                spacing: 6px;
                padding: 6px;
            }}
            QToolBar QToolButton {{
                color: {colors["text_primary"]};
                font-size: 11px;
                padding: 6px 10px;
                border: none;
                border-radius: 6px;
            }}
            QToolBar QToolButton:hover {{
                background-color: {colors["primary"]};
                color: white;
            }}
        """)

    def _apply_statusbar_theme(self, colors):
        """Применение темы к статусбару"""
        mw = self.main_window

        if not hasattr(mw, 'status_bar'):
            return

        mw.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {colors["surface_alt"]};
                color: {colors["text_secondary"]};
                border-top: 1px solid {colors["border"]};
                font-size: 10px;
            }}
        """)

    def _apply_left_panel_theme(self, colors, styles):
        """Применение темы к левой панели"""
        mw = self.main_window

        if hasattr(mw, 'search_input'):
            mw.search_input.setStyleSheet(styles["input"])

        if hasattr(mw, 'status_filter'):
            # простой стиль под тему
            mw.status_filter.setStyleSheet(f"""
                QComboBox {{
                    background: {colors["surface_alt"]};
                    color: {colors["text_primary"]};
                    border: 1px solid {colors["border"]};
                    border-radius: 6px;
                    padding: 4px;
                }}
                QComboBox QAbstractItemView {{
                    background: {colors["surface"]};
                    color: {colors["text_primary"]};
                    selection-background-color: {colors["primary"]};
                }}
            """)

        # Стили для массовых кнопок
        if hasattr(mw, 'bulk_close_btn'):
            bulk_button_style = f"""
                QPushButton {{
                    background-color: {colors["success"]};
                    border: none;
                    border-radius: 4px;
                    color: white;
                    font-weight: bold;
                    font-size: 10px;
                    padding: 6px 8px;
                }}
                QPushButton:hover {{
                    background-color: {colors["primary_hover"]};
                }}
                QPushButton:pressed {{
                    background-color: {colors["primary_pressed"]};
                }}
            """
            mw.bulk_close_btn.setStyleSheet(bulk_button_style)

        if hasattr(mw, 'bulk_delete_btn'):
            delete_button_style = f"""
                QPushButton {{
                    background-color: {colors["error"]};
                    border: none;
                    border-radius: 4px;
                    color: white;
                    font-weight: bold;
                    font-size: 10px;
                    padding: 6px 8px;
                }}
                QPushButton:hover {{
                    background-color: #dc2626;
                }}
                QPushButton:pressed {{
                    background-color: #b91c1c;
                }}
            """
            mw.bulk_delete_btn.setStyleSheet(delete_button_style)

    def get_status_color(self, status):
        """Получение цвета статуса"""
        colors = theme_manager.get_theme_styles()["colors"]

        status_colors = {
            "Новая": colors["primary"],
            "В работе": colors["success"],
            "Ожидает клиента": colors["warning"],
            "Ожидает оператора": colors["warning"],
            "Закрыта": colors["text_muted"]
        }

        return status_colors.get(status, colors["text_secondary"])

    def update_header_for_chat(self):
        """Обновление заголовка для текущего чата"""
        mw = self.main_window

        if not mw.active_chat:
            mw.ticket_label.setText("")
            mw.ticket_status_label.setText("")
            mw.operator_count_label.setText("")
            return

        mw.ticket_label.setText(mw.active_chat["id"])

        st = mw.active_chat["status"]
        if mw.left_chat:
            st = f"{st} • ПОКИНУТ"
        mw.ticket_status_label.setText(st)

        count_text = f"Операторов: {mw.active_chat.get('operators_count', 0)}"
        mw.operator_count_label.setText(count_text)

        # Обновляем цвета после изменения текста
        self._apply_header_theme(theme_manager.get_theme_styles()["colors"])
