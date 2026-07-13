import sys
import random
import string
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSlider, QCheckBox, QPushButton, QLineEdit, QGroupBox,
    QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette, QColor
import pyperclip


class PasswordGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Генератор паролей")
        self.setFixedSize(500, 450)

        # Центральный виджет и основной вертикальный layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(25, 25, 25, 25)

        # Заголовок
        title = QLabel("🔐 Генератор паролей")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Bold))
        main_layout.addWidget(title)

        # Группа настроек
        settings_group = QGroupBox("Настройки")
        settings_layout = QVBoxLayout(settings_group)

        # Длина пароля
        length_layout = QHBoxLayout()
        length_layout.addWidget(QLabel("Длина:"))
        self.length_slider = QSlider(Qt.Horizontal)
        self.length_slider.setMinimum(4)
        self.length_slider.setMaximum(64)
        self.length_slider.setValue(12)
        self.length_slider.setTickInterval(2)
        self.length_slider.setTickPosition(QSlider.TicksBelow)
        self.length_label = QLabel("12")
        self.length_label.setFixedWidth(30)
        self.length_slider.valueChanged.connect(
            lambda v: self.length_label.setText(str(v))
        )
        length_layout.addWidget(self.length_slider)
        length_layout.addWidget(self.length_label)
        settings_layout.addLayout(length_layout)

        # Чекбоксы для типов символов
        self.use_digits = QCheckBox("Цифры (0-9)")
        self.use_digits.setChecked(True)
        self.use_uppercase = QCheckBox("Заглавные буквы (A-Z)")
        self.use_uppercase.setChecked(True)
        self.use_lowercase = QCheckBox("Строчные буквы (a-z)")
        self.use_lowercase.setChecked(True)
        self.use_symbols = QCheckBox("Спецсимволы (!@#$%^&*)")
        self.use_symbols.setChecked(True)

        for cb in (self.use_digits, self.use_uppercase, self.use_lowercase, self.use_symbols):
            settings_layout.addWidget(cb)

        main_layout.addWidget(settings_group)

        # Кнопка генерации
        self.generate_btn = QPushButton("Сгенерировать пароль")
        self.generate_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.generate_btn.clicked.connect(self.generate_password)
        main_layout.addWidget(self.generate_btn)

        # Поле для вывода пароля
        self.password_display = QLineEdit()
        self.password_display.setReadOnly(True)
        self.password_display.setAlignment(Qt.AlignCenter)
        self.password_display.setFont(QFont("Courier New", 14, QFont.Bold))
        self.password_display.setStyleSheet("background-color: #2b2b2b; color: #ff4d4d; border: 2px solid #ff4d4d;")
        self.password_display.setPlaceholderText("Ваш пароль появится здесь")
        main_layout.addWidget(self.password_display)

        # Кнопка копирования
        copy_layout = QHBoxLayout()
        self.copy_btn = QPushButton("📋 Копировать в буфер")
        self.copy_btn.setEnabled(False)
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.strength_label = QLabel("Сложность: —")
        self.strength_label.setAlignment(Qt.AlignRight)
        copy_layout.addWidget(self.copy_btn)
        copy_layout.addWidget(self.strength_label)
        main_layout.addLayout(copy_layout)

        # Применяем тёмную тему и красные акценты через QSS
        self.apply_dark_theme()

    def apply_dark_theme(self):
        """Устанавливает тёмную тему с красными акцентами."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #e0e0e0;
                font-size: 12px;
            }
            QGroupBox {
                color: #e0e0e0;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
                margin-top: 10px;
                font-size: 13px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ff4d4d;
            }
            QCheckBox {
                color: #e0e0e0;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #2d2d2d;
                border: 1px solid #555;
            }
            QCheckBox::indicator:checked {
                background-color: #ff4d4d;
                border: 1px solid #ff4d4d;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #3a3a3a;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ff4d4d;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: #ff4d4d;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #ff4d4d;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff4d4d;
                color: #1e1e1e;
            }
            QPushButton:pressed {
                background-color: #cc0000;
            }
            QPushButton:disabled {
                background-color: #3a3a3a;
                border-color: #555;
                color: #777;
            }
            QLineEdit {
                background-color: #2b2b2b;
                color: #ff4d4d;
                border: 2px solid #ff4d4d;
                border-radius: 5px;
                padding: 6px;
                font-size: 14px;
            }
        """)

    def generate_password(self):
        """Генерирует пароль на основе выбранных настроек."""
        length = self.length_slider.value()

        # Сбор разрешённых символов
        char_pool = ""
        if self.use_lowercase.isChecked():
            char_pool += string.ascii_lowercase
        if self.use_uppercase.isChecked():
            char_pool += string.ascii_uppercase
        if self.use_digits.isChecked():
            char_pool += string.digits
        if self.use_symbols.isChecked():
            char_pool += "!@#$%^&*()_+-=[]{}|;:,.<>?/~"

        if not char_pool:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы один тип символов!")
            return

        # Генерация пароля
        password = ''.join(random.choice(char_pool) for _ in range(length))
        self.password_display.setText(password)
        self.copy_btn.setEnabled(True)

        # Оценка сложности
        strength = self.evaluate_strength(password)
        self.strength_label.setText(f"Сложность: {strength}")

    def evaluate_strength(self, pwd):
        """Оценивает сложность пароля."""
        score = 0
        if len(pwd) >= 12:
            score += 1
        if any(c.islower() for c in pwd):
            score += 1
        if any(c.isupper() for c in pwd):
            score += 1
        if any(c.isdigit() for c in pwd):
            score += 1
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/~" for c in pwd):
            score += 1

        if score <= 2:
            return "Слабый"
        elif score == 3:
            return "Средний"
        elif score == 4:
            return "Хороший"
        else:
            return "Отличный"

    def copy_to_clipboard(self):
        """Копирует пароль в буфер обмена."""
        pwd = self.password_display.text()
        if pwd:
            pyperclip.copy(pwd)
            QMessageBox.information(self, "Готово", "Пароль скопирован в буфер обмена!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Устанавливаем палитру для принудительного тёмного фона (дополнительно к QSS)
    app.setStyle("Fusion")
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.WindowText, QColor(224, 224, 224))
    dark_palette.setColor(QPalette.Base, QColor(43, 43, 43))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(224, 224, 224))
    dark_palette.setColor(QPalette.ToolTipText, QColor(224, 224, 224))
    dark_palette.setColor(QPalette.Text, QColor(224, 224, 224))
    dark_palette.setColor(QPalette.Button, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.ButtonText, QColor(224, 224, 224))
    dark_palette.setColor(QPalette.BrightText, QColor(255, 77, 77))
    dark_palette.setColor(QPalette.Highlight, QColor(255, 77, 77))
    dark_palette.setColor(QPalette.HighlightedText, QColor(30, 30, 30))
    app.setPalette(dark_palette)

    window = PasswordGenerator()
    window.show()
    sys.exit(app.exec_())