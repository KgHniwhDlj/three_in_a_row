import random

from PyQt5.QtCore import QPoint, QSize, QPropertyAnimation, QEasingCurve, Qt
from PyQt5.QtGui import QPixmap, QIcon, QFontDatabase, QFont
from PyQt5.QtWidgets import (
    QLabel,
    QFrame, QPushButton, QWidget
)

from GUI.tile_label import TileLabel
from core.audio_manager import AudioManager
from core.board import Board
from core.enums import Bonus
from core.setting_deploy import get_resource_path

audio = AudioManager.instance()


class BoardView(QWidget):
    ROWS = 8
    COLS = 7
    CELL_SIZE = 60
    GRID_ORIGIN = QPoint(40, 300)

    ICON_PATH = get_resource_path("assets/icon.png")
    BACKGROUND_PATH = get_resource_path("assets/game_background.png")
    TITLE_PATH = get_resource_path("assets/board.png")
    SETTINGS_ICON = get_resource_path("assets/buttons/settings.png")
    FONT_PATH = get_resource_path("assets/FontFont.otf")

    TILE_IMAGES = {
        name: get_resource_path(f"assets/elements/{name}.png")
        for name in ("orange", "purple", "red", "yellow")
    }
    BLOCK_IMAGES = [
        get_resource_path(f"assets/block{i}.png")
        for i in (1, 2)
    ]

    def __init__(self):
        super().__init__()
        self.setEnabled(False)

        self.setFocusPolicy(Qt.NoFocus)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)

        self.board = None
        self.animations = []
        self.selected_tile = None
        self.tile_labels = {}
        self._load_fonts()
        self._init_window()
        self._init_background()
        self._init_title()
        self._init_control_frames()
        self._init_settings_button()
        self._init_board_container()
        self._init_grid()
        self._init_digit_labels()

        self.elapsed_seconds = 0

        self.display_number('timer', self.elapsed_seconds)
        self.score = 0
        self.display_number('score', self.score)

    def _load_fonts(self):
        font_id = QFontDatabase.addApplicationFont(self.FONT_PATH)
        families = QFontDatabase.applicationFontFamilies(font_id)
        self.font_family = families[0] if families else self.font().family()

    def _init_window(self):
        self.setWindowTitle("Three in row: animate window")
        self.setGeometry(700, 100, 500, 880)
        self.setWindowIcon(QIcon(self.ICON_PATH))
        self.setFixedSize(500, 880)

    def _init_background(self):
        lbl = QLabel(self)
        pix = QPixmap(self.BACKGROUND_PATH).scaled(self.width(), self.height())
        lbl.setPixmap(pix)
        lbl.setGeometry(0, 0, self.width(), self.height())
        lbl.lower()

    def _init_title(self):
        lbl = QLabel(self)
        pix = QPixmap(self.TITLE_PATH).scaled(440, 200)
        lbl.setPixmap(pix)
        lbl.setGeometry(30, 0, 440, 200)
        lbl.raise_()

    def _init_control_frames(self):
        coords = {'timer': (100, 70), 'score': (280, 70)}
        self.control_frames = {}
        for key, (x, y) in coords.items():
            frame = QFrame(self)
            frame.setGeometry(x, y, 120, 85)
            frame.setStyleSheet(
                "QFrame { background-color: rgb(254,243,219); "
                "border:1px solid #000; border-radius:6px;}"
            )
            self.control_frames[key] = frame
            lbl = QLabel('Время' if key == 'timer' else 'Счёт', self)
            lbl.setFont(QFont(self.font_family, 18))
            lbl.setStyleSheet("color: #000;")
            lbl.setGeometry(x + 20, 20, 200, 50)
            lbl.raise_()

    def _init_settings_button(self):
        btn = QPushButton(self)
        btn.setIcon(QIcon(self.SETTINGS_ICON))
        btn.setIconSize(QSize(40, 40))
        btn.setGeometry(420, 140, 40, 40)
        btn.setFlat(True)

    def _init_board_container(self):
        x, y = self.GRID_ORIGIN.x() - 10, self.GRID_ORIGIN.y() - 10
        w, h = self.COLS * self.CELL_SIZE + 20, self.ROWS * self.CELL_SIZE + 20
        frame = QFrame(self)
        frame.setGeometry(x, y, w, h)
        frame.setStyleSheet(
            "QFrame { background-color: rgba(14,99,167,200); "
            "border:3px solid #000; border-radius:6px;}"
        )
        frame.lower()
        self.board_container = frame

    def _init_grid(self):
        self.background_labels = []
        for r in range(self.ROWS):
            row_labels = []
            for c in range(self.COLS):
                lbl = QLabel(self)
                lbl.setPixmap(
                    QPixmap(self.BLOCK_IMAGES[(r + c) % 2])
                    .scaled(self.CELL_SIZE, self.CELL_SIZE)
                )
                lbl.setGeometry(
                    self.GRID_ORIGIN.x() + c * self.CELL_SIZE,
                    self.GRID_ORIGIN.y() + r * self.CELL_SIZE,
                    self.CELL_SIZE, self.CELL_SIZE
                )
                lbl.raise_()
                row_labels.append(lbl)
            self.background_labels.append(row_labels)

    def _init_digit_labels(self):
        self.digit_labels = {'timer': [], 'score': []}

    def _animate_fall(self, tile: TileLabel, target_row: int, finished=None):
        start = tile.pos()
        end = QPoint(start.x(),
                     self.GRID_ORIGIN.y() + target_row * self.CELL_SIZE)

        dist = end.y() - start.y()
        dur = 100 + dist * 2
        anim = QPropertyAnimation(tile, b'pos', self)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setDuration(dur)
        anim.setEasingCurve(QEasingCurve.OutBounce)

        if finished:
            anim.finished.connect(finished)
        anim.start()
        self.animations.append(anim)

    def display_number(self, kind, value, color: str = None, x=None, y=None):
        _colors = ['blue', 'red', 'green', 'orange', 'purple', 'yellow']
        if color is None:
            color = random.choice(_colors)
        if x is None or y is None:
            coords = {'timer': (125, 95), 'score': (305, 95)}
            x, y = coords[kind]
        for lbl in self.digit_labels[kind]:
            lbl.deleteLater()
        self.digit_labels[kind].clear()
        for i, ch in enumerate(str(value)):
            path = get_resource_path(f"assets/score/{color}/{ch}.png")
            pix = QPixmap(path)
            lbl = QLabel(self)
            lbl.setPixmap(pix)
            w, h = pix.width(), pix.height()
            lbl.setGeometry(x + i * w, y, w, h)
            lbl.raise_()
            lbl.show()
            self.digit_labels[kind].append(lbl)

    def update_score(self, score: int):
        self.score = score
        self.display_number('score', self.score)

    def tick_clock(self, elapsed_seconds: int):
        self.elapsed_seconds = elapsed_seconds
        self.display_number('timer', self.elapsed_seconds)

    def render_from_board(self, first=False):
        for lbl in self.tile_labels.values():
            lbl.deleteLater()
        self.tile_labels.clear()

        for r in range(self.ROWS):
            for c in range(self.COLS):
                elem = self.board.cell(r, c)
                pix = self._pix_for_elem(elem)
                lbl = TileLabel(self, elem)
                lbl.setPixmap(pix)
                x = self.GRID_ORIGIN.x() + c * self.CELL_SIZE
                y = self.GRID_ORIGIN.y() + (-1 if first else r) * self.CELL_SIZE
                lbl.setGeometry(x, y, self.CELL_SIZE, self.CELL_SIZE)
                lbl.raise_()
                lbl.show()
                self.tile_labels[(r, c)] = lbl
                if first:
                    self._animate_fall(lbl, r)

    def update_board(self, board: Board, first=False):
        self.board = board
        self.render_from_board(first)

    def _pix_for_elem(self, elem):
        if elem is None:
            return None
        root = "assets/elements"
        if elem.bonus == Bonus.NONE:
            img = f"{root}/{elem.color.value}.png"
        elif elem.bonus == Bonus.BOMB:
            img = f"{root}/bomb.png"
        else:
            axis = "h" if elem.bonus == Bonus.ROCKET_H else "v"
            img = f"{root}/rocket_{axis}.png"
        return QPixmap(get_resource_path(img)).scaled(self.CELL_SIZE, self.CELL_SIZE)
