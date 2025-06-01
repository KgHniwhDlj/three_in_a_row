import threading

from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon, QFont, QFontDatabase, QPixmap
from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QSpinBox, QComboBox, QListWidget
)

from GUI.game_window import GameWindow
from core.audio_manager import AudioManager
from core.server import Server
from core.setting_deploy import get_resource_path
from logger import logger

audio = AudioManager.instance()


class CreateGameWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.server = None
        self.stop_event = threading.Event()
        self.selected_mode = None
        self.setWindowOpacity(0.0)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setModal(True)
        self.setFixedSize(400, 500)

        # шрифт
        fid = QFontDatabase.addApplicationFont(get_resource_path("assets/FontFont.otf"))
        fams = QFontDatabase.applicationFontFamilies(fid)
        self.font = fams[0] if fams else self.font().family()

        # фон
        bg = QLabel(self)
        bg.setStyleSheet(
            "background: rgb(255,204,141);"
            "border:6px solid #af5829;"
            "border-radius:20px;"
        )
        bg.setGeometry(20, 40, 360, 460)
        bg.lower()

        # заголовок
        pic = QLabel(self)
        p = QPixmap(get_resource_path("assets/setting_title.png")) \
            .scaled(300, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        pic.setPixmap(p)
        pic.setGeometry(50, 0, 300, 100)

        title = QLabel("Создать игру", self)
        title.setFont(QFont(self.font, 16, QFont.Bold))
        title.setStyleSheet("color: rgb(230,230,40);")
        title.setGeometry(105, 20, 200, 50)

        close = QPushButton(self)
        close.setIcon(QIcon(get_resource_path("assets/buttons/cancel.png")))
        close.setIconSize(QSize(60, 60))
        close.setFlat(True)
        close.setGeometry(340, 15, 60, 60)
        close.clicked.connect(self.closeEvent)

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

        self.players_list = QListWidget(self)
        self.players_list.setFont(QFont(self.font, 12))
        self.players_list.setStyleSheet(
            "background-color: rgb(254,243,219); border:2px solid #af5829; border-radius:6px;"
        )
        self.players_list.setGeometry(50, 330, 300, 100)
        self.players_list.hide()

        self.lbl_mode = QLabel("Выберите режим:", self)
        self.lbl_mode.setFont(QFont(self.font, 14))
        self.lbl_mode.setGeometry(50, 200, 300, 30)
        self.lbl_mode.hide()

        self.mode_combo = QComboBox(self)
        self.mode_combo.setFont(QFont(self.font, 12))
        self.mode_combo.addItems(["-- режим --", "На время"])
        self.mode_combo.setStyleSheet(
            "background-color: rgb(254,243,219); border:2px solid #af5829; border-radius:6px;"
        )
        self.mode_combo.setGeometry(50, 230, 300, 30)
        self.mode_combo.currentIndexChanged.connect(self._on_select_mode)
        self.mode_combo.hide()

        self.spin_time = QSpinBox(self)
        self.spin_time.setRange(20, 999)
        self.spin_time.setSuffix(" с")
        self.spin_time.setFont(QFont(self.font, 12))
        self.spin_time.setGeometry(50, 280, 300, 30)
        # self.spin_time.clicked.connect(self._select_time)
        self.spin_time.setStyleSheet(
            "background-color: rgb(254,243,219); border:2px solid #af5829; border-radius:6px;"
        )
        self.spin_time.hide()

        self.btn_generate = QPushButton("Сгенерировать код", self)
        self.btn_generate.setFont(QFont(self.font, 12))
        self.btn_generate.setGeometry(50, 280, 300, 30)
        self.btn_generate.clicked.connect(self._on_generate)
        self.btn_generate.setStyleSheet(
            "background-color: rgb(254,243,219); border:2px solid #af5829; border-radius:6px;"
        )
        self.btn_generate.hide()

        # 4) поле кода и кнопка старт
        self.lbl_code = QLabel("Код доступа: ", self)
        self.lbl_code.setFont(QFont(self.font, 14))
        self.lbl_code.setGeometry(50, 280, 300, 30)
        self.lbl_code.setAlignment(Qt.AlignLeft)
        self.lbl_code.hide()

        self.btn_start = QPushButton("Начать игру", self)
        self.btn_start.setFont(QFont(self.font, 14))
        self.btn_start.setGeometry(50, 440, 300, 40)
        self.btn_start.setStyleSheet(
            "background-color: rgb(254,243,219); border:2px solid #af5829; border-radius:6px;"
        )
        self.btn_start.clicked.connect(self._on_start)
        self.btn_start.hide()

        self._animate_show()

    def _on_nick_changed(self, text):
        if len(text) >= 1:
            self.mode_combo.show()
            self.lbl_mode.show()
        else:
            self.mode_combo.hide()
            self.lbl_mode.hide()

    def _on_select_mode(self, idx):
        self.nick_edit.setDisabled(True)
        self.mode_combo.setDisabled(True)
        if idx == 1:
            logger.info("Choose time mode")
            self.spin_time.show()
            self.btn_generate.show()
            self.btn_generate.setGeometry(50, 330, 300, 30)
            self.selected_mode = "time"
        elif idx == 2:
            logger.info("Choose chess mode")
            self.btn_generate.show()
            self.selected_mode = "chess"

    def _on_generate(self):
        self.spin_time.setDisabled(True)
        self.server = Server(nickname=self.nick_edit.text(), mode=self.selected_mode,
                             time=self.spin_time.value() if self.selected_mode == "time" else 999)
        self.lbl_code.setText(f"Код доступа {self.server.session_code}")
        self.btn_generate.setVisible(False)
        self.players_list.show()
        if self.selected_mode == "time":
            self.lbl_code.setGeometry(50, 330, 300, 30)
            self.players_list.setGeometry(50, 360, 300, 70)
        threading.Thread(target=self.server.start, daemon=True).start()
        threading.Thread(target=self._update_players_list, daemon=True).start()

        self.lbl_code.show()

    def _update_players_list(self):
        while not self.stop_event.is_set():
            self.players_list.clear()
            for nick in self.server.clients.keys():
                self.players_list.addItem(nick)
            if len(self.server.clients) >= self.server.value_players:
                self.btn_start.show()
            else:
                self.btn_start.hide()
            self.stop_event.wait(1)

    def closeEvent(self, event):
        if self.server:
            self.server.shutdown(None, None)
        self.reject()

    def _on_start(self):
        audio.switch_to_game()
        logger.info("Начинаем игру")
        self.server.gui = GameWindow(main_window=self.main_window)
        self.server.gui.show()
        self.server.gui.ctrl = self.server.ctrl
        self.server.ctrl.new_game([self.server.nickname, *self.server.clients])
        self.accept()
        self.accept()

    def _animate_show(self):
        fade = QPropertyAnimation(self, b"windowOpacity", self)
        fade.setDuration(300)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.InOutQuad)
        fade.start(QPropertyAnimation.DeleteWhenStopped)
