from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon, QFont, QPixmap, QFontDatabase
from PyQt5.QtWidgets import QPushButton, QLabel, QWidget

from GUI.create_game_window import CreateGameWindow
from GUI.game_window import GameWindow
from GUI.join_game_window import JoinGameWindow
from GUI.settings_window import SettingsWindow
from core.audio_manager import AudioManager
from core.setting_deploy import get_resource_path
from logger import logger

audio = AudioManager.instance()


class MainWindow(QWidget):
    WIDTH, HEIGHT = 500, 880

    def __init__(self):
        super().__init__()
        self.game_window = None
        self.setWindowTitle("Three in row")
        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setWindowIcon(QIcon(get_resource_path("assets/icon.png")))
        self._load_font()
        self._make_background()
        self._make_ui()

    def _load_font(self):
        fid = QFontDatabase.addApplicationFont(get_resource_path("assets/FontFont.otf"))
        fams = QFontDatabase.applicationFontFamilies(fid)
        self.font_family = fams[0] if fams else self.font().family()

    def _make_background(self):
        bg = QLabel(self)
        bg.setPixmap(QPixmap(get_resource_path("assets/start_background.png"))
                     .scaled(self.WIDTH, self.HEIGHT))
        bg.setGeometry(0, 0, self.WIDTH, self.HEIGHT)
        bg.lower()

    def _make_ui(self):
        circle = QLabel(self)
        circle_pix = QPixmap(get_resource_path("assets/circle.png")).scaled(380, 380,
                                                                            Qt.KeepAspectRatio, Qt.SmoothTransformation)
        circle.setPixmap(circle_pix)
        circle.move((self.WIDTH - circle_pix.width()) // 2, 90)

        self.create_btn = self._menu_button("Создать игру",
                                            "assets/buttons/start.png",
                                            ypos=550, func_handler=self._create_game)
        self.join_btn = self._menu_button("Присоединиться",
                                          "assets/buttons/start.png",
                                          ypos=660, func_handler=self._join_game)

        self.solo_btn = self._menu_button("Соло игра",
                                          "assets/buttons/start.png",
                                          ypos=775, func_handler=self._solo_game)

        sett = self._icon_btn("assets/buttons/settings.png", 60, 60,
                              self.WIDTH - 70, 15, self._open_settings)
        close = self._icon_btn("assets/buttons/exit.png", 60, 60,
                               15, 15, self.close)

    def _menu_button(self, text, icon_path, ypos, func_handler=None):
        btn = QPushButton(self)
        btn.setIcon(QIcon(get_resource_path(icon_path)))
        btn.setIconSize(QSize(400, 90))
        btn.setFixedSize(400, 90)
        btn.move((self.WIDTH - 400) // 2, ypos)
        btn.setFlat(True)
        btn.clicked.connect(func_handler)

        lbl = QLabel(text, self)
        lbl.setFont(QFont(self.font_family, 20, QFont.Bold))
        lbl.setStyleSheet("color: #af5829;")
        lbl.adjustSize()
        lbl.move(btn.x() + (btn.width() - lbl.width()) // 2,
                 btn.y() + (btn.height() - lbl.height()) // 2)
        lbl.raise_()
        lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        return btn

    def _icon_btn(self, path, w, h, x, y, slot):
        b = QPushButton(self)
        b.setIcon(QIcon(get_resource_path(path)))
        b.setIconSize(QSize(w, h))
        b.setFlat(True)
        b.setGeometry(x, y, w, h)
        b.clicked.connect(slot)
        return b

    def _open_settings(self):
        dlg = SettingsWindow(self, is_home_visible=False)
        dlg.move(self.x() + (self.width() - dlg.width()) // 2,
                 self.y() + (self.height() - dlg.height()) // 2)
        dlg.exec_()

    def _create_game(self):
        logger.info("Создание новой игры")
        create_game_window = CreateGameWindow(self)
        create_game_window.move(self.x() + (self.width() - create_game_window.width()) // 2,
                                self.y() + (self.height() - create_game_window.height()) // 2)
        create_game_window.exec_()

    def _join_game(self):
        logger.info("Присоединение к игре")
        join_game_window = JoinGameWindow(self)
        join_game_window.move(self.x() + (self.width() - join_game_window.width()) // 2,
                              self.y() + (self.height() - join_game_window.height()) // 2)
        join_game_window.exec_()

    def _solo_game(self):
        audio.switch_to_game()
        logger.info("Присоединение к игре")
        self.game_window = GameWindow(main_window=self, solo=True)
        self.game_window.show()
