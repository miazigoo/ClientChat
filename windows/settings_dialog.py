from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QRadioButton, QComboBox
from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import QColorDialog
from styles.theme_manager import theme_manager, ThemeType

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.resize(360, 220)

        lay = QVBoxLayout(self)
        # Тема
        lay.addWidget(QLabel("Тема:"))
        self.rb_dark = QRadioButton("Темная")
        self.rb_light = QRadioButton("Светлая")
        lay.addWidget(self.rb_dark); lay.addWidget(self.rb_light)

        self.rb_dark.setChecked(theme_manager.get_current_theme() == ThemeType.DARK)
        self.rb_light.setChecked(theme_manager.get_current_theme() == ThemeType.LIGHT)

        # Акцент
        lay.addWidget(QLabel("Акцент:"))
        self.accent = QComboBox()
        self.accent.addItems(["blue", "green", "purple", "orange", "custom"])
        self.accent.setCurrentText(theme_manager.get_accent())
        lay.addWidget(self.accent)

        self.custom_btn = QPushButton("Выбрать свой цвет...")
        lay.addWidget(self.custom_btn)
        self.custom_btn.clicked.connect(self.pick_custom_color)

        # Кнопки
        btns = QHBoxLayout()
        btns.addStretch()
        ok = QPushButton("Сохранить")
        cancel = QPushButton("Отмена")
        btns.addWidget(ok); btns.addWidget(cancel)
        lay.addLayout(btns)

        ok.clicked.connect(self.apply_and_close)
        cancel.clicked.connect(self.reject)

    def pick_custom_color(self):
        c = QColorDialog.getColor()
        if c.isValid():
            theme_manager.set_custom_accent(c.name())
            self.accent.setCurrentText("custom")

    def apply_and_close(self):
        # Тема
        theme_manager.set_theme(ThemeType.DARK if self.rb_dark.isChecked() else ThemeType.LIGHT)
        # Акцент
        acc = self.accent.currentText()
        if acc != "custom":
            theme_manager.set_accent(acc)

        # Сохраним в QSettings
        st = QSettings("SupportChat", "ClientApp")
        st.setValue("theme", "dark" if self.rb_dark.isChecked() else "light")
        st.setValue("accent", theme_manager.get_accent())
        if theme_manager.get_accent() == "custom":
            st.setValue("custom_primary", theme_manager.get_theme_styles()["colors"]["primary"])

        self.accept()
