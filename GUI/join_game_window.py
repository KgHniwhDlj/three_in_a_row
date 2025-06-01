import threading

from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon, QFont, QFontDatabase, QPixmap
from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton
)

from GUI.game_window import GameWindow
from core.audio_manager import AudioManager
from core.client import Client
from core.setting_deploy import get_resource_path
from logger import logger

audio = AudioManager.instance()


class JoinGameWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.client = None
        self.server = None
        self.stop_event = threading.Event()
        self.selected_mode = None
        self.setWindowOpacity(0.0)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setModal(True)
        self.setFixedSize(400, 500)

        fid = QFontDatabase.addApplicationFont(get_resource_path("assets/FontFont.otf"))
        fams = QFontDatabase.applicationFontFamilies(fid)
        self.font = fams[0] if fams else self.font().family()

        bg = QLabel(self)
        bg.setStyleSheet(
            "background: rgb(255,204,141);"
            "border:6px solid #af5829;"
            "border-radius:20px;"
        )
        bg.setGeometry(20, 40, 360, 460)
        bg.lower()

        pic = QLabel(self)
        p = QPixmap(get_resource_path("assets/setting_title.png")) \
            .scaled(300, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        pic.setPixmap(p)
        pic.setGeometry(50, 0, 300, 100)

        title = QLabel("Присоединит-\n    ся к игре", self)
        title.setFont(QFont(self.font, 16, QFont.Bold))
        title.setStyleSheet("color: rgb(230,230,40);")
        title.setGeometry(105, 20, 200, 60)

        close = QPushButton(self)
        close.setIcon(QIcon(get_resource_path("assets/buttons/cancel.png")))
        close.setIconSize(QSize(60, 60))
        close.setFlat(True)
        close.setGeometry(340, 15, 60, 60)
        close.clicked.connect(self.reject)

        lbl_n = QLabel("Ваш никнейм:", self)
        lbl_n.setFont(QFont(self.font, 14))
        lbl_n.setGeometry(50, 130, 150, 30)

        self.nick_edit = QLineEdit(self)
        self.nick_edit.setStyleSheet(
            "background-color: rgb(254,243,219); border:2px solid #af5829; border-radius:6px;"
        )
        self.nick_edit.setFont(QFont(self.font, 12))
        self.nick_edit.setPlaceholderText("Введите никнейм")
        self.nick_edit.setGeometry(50, 160, 300, 30)
        self.nick_edit.textChanged.connect(self._on_nick_changed)

        self.lbl_code = QLabel("Пригласительный код:", self)
        self.lbl_code.setFont(QFont(self.font, 14))
        self.lbl_code.setGeometry(50, 200, 300, 30)
        self.lbl_code.hide()
        self.code_edit = QLineEdit(self)
        self.code_edit.setStyleSheet(
            "background-color: rgb(254,243,219); border:2px solid #af5829; border-radius:6px;"
        )
        self.code_edit.setFont(QFont(self.font, 12))
        self.code_edit.setPlaceholderText("Введите код")
        self.code_edit.setGeometry(50, 230, 300, 30)
        self.code_edit.textChanged.connect(self._on_code_changed)
        self.code_edit.hide()

        self.join_button = QPushButton("Присоединится к игре", self)
        self.join_button.setFont(QFont(self.font, 14))
        self.join_button.setGeometry(50, 280, 300, 40)
        self.join_button.setStyleSheet(
            "background-color: rgb(254,243,219); border:2px solid #af5829; border-radius:6px;"
        )
        self.join_button.clicked.connect(self.join_game)
        self.join_button.hide()

        self.status_label = QLabel("", self)
        self.status_label.setFont(QFont(self.font, 14))
        self.status_label.setGeometry(50, 340, 300, 80)
        self.status_label.setVisible(False)
        self._animate_show()

    def _on_nick_changed(self, text):
        if len(text) >= 1:
            self.lbl_code.show()
            self.code_edit.show()
        else:
            self.lbl_code.hide()
            self.code_edit.hide()

    def _on_code_changed(self, text):
        if len(text) >= 1:
            self.join_button.show()
        else:
            self.join_button.hide()

    def join_game(self):
        session_code = self.code_edit.text().strip()
        if not session_code:
            self.show_error("Введите код!")
            return

        self.show_status("Подключение...")

        nickname = self.nick_edit.text()
        self.client = Client(session_code, nickname, self)

    def show_error(self, message):
        self.status_label.setText(message)
        self.status_label.setStyleSheet("font-size: 18px; color: red; font-weight: bold;")
        self.status_label.setVisible(True)
        self.join_button.setVisible(False)
        self.nickname_combo.setCurrentIndex(0)
        self.nickname_combo.setDisabled(False)

    def show_success(self, message="Вы успешно подключились!/n Ожидайте начала игры."):
        self.status_label.setText(message)
        self.status_label.setStyleSheet("font-size: 14px; color: green; font-weight: bold;")
        self.status_label.setVisible(True)

    def show_status(self, message):
        self.status_label.setText(message)
        self.status_label.setStyleSheet("font-size: 14px; color: blue; font-weight: bold;")
        self.status_label.setVisible(True)

    def start_game(self):
        audio.switch_to_game()
        self.client.gui = GameWindow(main_window=self.main_window)
        self.client.gui.ctrl = self.client.ctrl
        self.client.gui.apply_state("start_game")
        self.client.gui.show()
        logger.info("Game start")
        self.accept()

    def _animate_show(self):
        fade = QPropertyAnimation(self, b"windowOpacity", self)
        fade.setDuration(300)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.InOutQuad)
        fade.start(QPropertyAnimation.DeleteWhenStopped)
