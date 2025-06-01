from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtWidgets import QDialog, QLabel, QPushButton

from core.setting_deploy import get_resource_path


class EndGameWindow(QDialog):
    def __init__(self, parent=None, player_name: str = "", message: str = "", score: int = 0):
        super().__init__(parent)
        self.setWindowOpacity(0.0)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setModal(True)
        self.setFixedSize(400, 300)

        bg = QLabel(self)
        bg.setStyleSheet(
            "background: rgb(255,204,141);"
            "border:6px solid #af5829;"
            "border-radius:20px;"
        )
        bg.setGeometry(20, 20, 360, 260)

        fid = QFontDatabase.addApplicationFont(get_resource_path("assets/FontFont.otf"))
        fams = QFontDatabase.applicationFontFamilies(fid)
        font_family = fams[0] if fams else self.font().family()

        title = QLabel("Увы, но все", self)
        title.setFont(QFont(font_family, 18, QFont.Bold))
        title.setStyleSheet("color: rgb(30, 31, 34);")
        title.setGeometry(100, 30, 200, 40)
        title.setAlignment(Qt.AlignCenter)

        lbl_name = QLabel(f"Игрок: {player_name}", self)
        lbl_name.setFont(QFont(font_family, 14))
        lbl_name.setStyleSheet("color: #000;")
        lbl_name.setGeometry(50, 80, 300, 30)
        lbl_name.setAlignment(Qt.AlignCenter)

        lbl_score = QLabel(f"Счет игрока: {score}", self)
        lbl_score.setFont(QFont(font_family, 14))
        lbl_score.setStyleSheet("color: #000;")
        lbl_score.setGeometry(50, 120, 300, 30)
        lbl_score.setAlignment(Qt.AlignCenter)

        lbl_msg = QLabel(message, self)
        lbl_msg.setFont(QFont(font_family, 16))
        lbl_msg.setStyleSheet("color: #333;")
        lbl_msg.setGeometry(50, 140, 300, 60)
        lbl_msg.setWordWrap(True)
        lbl_msg.setAlignment(Qt.AlignCenter)

        btn_close = QPushButton("OK", self)
        btn_close.setFont(QFont(font_family, 14))
        btn_close.setGeometry(150, 200, 100, 40)
        btn_close.setStyleSheet(
            "background-color: rgb(254,243,219);"
            "border:2px solid #af5829;"
            "border-radius:6px;"
        )
        btn_close.clicked.connect(self.accept)

    def showEvent(self, e):
        super().showEvent(e)
        fade = QPropertyAnimation(self, b"windowOpacity", self)
        fade.setDuration(300)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.InOutQuad)
        fade.start(QPropertyAnimation.DeleteWhenStopped)
