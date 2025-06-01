import random
from typing import Set, Tuple, List

from PyQt5.QtCore import QPoint, QSize, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QTimer, Qt
from PyQt5.QtGui import QPixmap, QIcon, QFontDatabase, QFont
from PyQt5.QtWidgets import (
    QLabel,
    QFrame, QPushButton, QMessageBox, QWidget
)

from GUI.board_view import BoardView
from GUI.end_game_window import EndGameWindow
from GUI.explosion_label import ExplosionLabel
from GUI.settings_window import SettingsWindow
from GUI.tile_label import TileLabel
from core.audio_manager import AudioManager
from core.board import Board
from core.enums import Bonus, Color
from core.game_controller import GameController
from core.setting_deploy import get_resource_path
from logger import logger

audio = AudioManager.instance()


class GameWindow(QWidget):
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

    def __init__(self, ctrl: GameController = None, main_window=None, solo=False):
        super().__init__()
        self.solo_game = solo
        print(self.solo_game)
        self.end_game_window = None
        self.pending_animations = 0
        self._on_all_animations = None
        self.waiting_overlay = None
        self.opp_view = None
        self.old_b = None
        self.old_a = None
        self.main_window = main_window
        self.main_window.hide()
        self.ctrl = ctrl
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
        if self.solo_game:
            self.board = Board()
            self.render_from_board(first=True)
        self.elapsed_seconds = 0

        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(1000)
        self._clock_timer.timeout.connect(self._tick_clock)
        self._clock_timer.start()

        self.display_number('timer', self.elapsed_seconds)
        self.score = 0
        self.display_number('score', self.score)

    def _load_fonts(self):
        font_id = QFontDatabase.addApplicationFont(self.FONT_PATH)
        families = QFontDatabase.applicationFontFamilies(font_id)
        self.font_family = families[0] if families else self.font().family()

    def _init_window(self):
        self.setWindowTitle("Three in row")
        self.setGeometry(100, 100, 500, 880)
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
        btn.clicked.connect(self._open_settings)

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
        self.pending_animations += 1
        if finished:
            anim.finished.connect(finished)
            self.pending_animations -= 1
            self._check_animations_done()
        anim.start()
        self.animations.append(anim)

    def handle_swap_request(self, a_lbl: TileLabel, b_lbl: TileLabel):
        if self.solo_game:
            pass
        else:
            if self.ctrl.mode != "time" and not self.ctrl.is_my_step:
                return
        if abs(a_lbl.row - b_lbl.row) + abs(a_lbl.col - b_lbl.col) != 1:
            return
        audio.play_sound("swap")
        self.old_a = (a_lbl.row, a_lbl.col)
        self.old_b = (b_lbl.row, b_lbl.col)
        self._animate_swap(a_lbl, b_lbl,
                           lambda: self._after_swap_logic(a_lbl, b_lbl))

    def _after_swap_logic(self, a_lbl, b_lbl):
        a = (a_lbl.row, a_lbl.col)
        b = (b_lbl.row, b_lbl.col)
        success, removed, bonuses = self.board.swap(a, b)
        if not self.solo_game:
            if self.ctrl.mode == "chess":
                self.ctrl.swap(a_lbl=self.old_a, b_lbl=self.old_b, success=success,
                               removed=removed, bonuses=bonuses)
        if not success:
            self._animate_swap(a_lbl, b_lbl, on_finished=None)
            return

        audio.play_sound("nice_swap")
        if not bonuses and removed:
            self._update_score(len(removed))
            for r, c in removed:
                lbl = self.tile_labels.pop((r, c), None)

                if lbl and lbl.element.bonus in [Bonus.ROCKET_H, Bonus.ROCKET_V]:
                    self._fire_rocket(r, c, lbl.element.bonus)
                    lbl.deleteLater()
                elif lbl:
                    explosion = ExplosionLabel(self, lbl.element.color.value, lbl.pos(), self.CELL_SIZE, fps=100,
                                               bonus=lbl.element.bonus)

                    lbl.deleteLater()

                    explosion.raise_()
                    explosion.show()
                    if lbl.element.bonus == Bonus.BOMB:
                        audio.play_sound("boom")
                    else:
                        audio.play_sound("removed")
            self._update_game()
            return

        self._update_score(len(removed))
        for r, c in removed:
            lbl = self.tile_labels.pop((r, c), None)
            if not lbl:
                continue

            explosion = ExplosionLabel(self, lbl.element.color.value, lbl.pos(), self.CELL_SIZE, fps=100)

            lbl.deleteLater()

            explosion.raise_()
            explosion.show()
            audio.play_sound("removed")

        for r, c, bonus in bonuses:
            elem = self.board.cell(r, c)
            lbl = TileLabel(self, elem)
            pix = self._pix_for_elem(elem)
            lbl.setPixmap(pix)
            x = self.GRID_ORIGIN.x() + c * self.CELL_SIZE
            y = self.GRID_ORIGIN.y() + r * self.CELL_SIZE
            lbl.setGeometry(x, y, self.CELL_SIZE, self.CELL_SIZE)
            lbl.raise_()
            lbl.show()
            self.tile_labels[(r, c)] = lbl
            audio.play_sound("add_bonus")

        self._update_game()

    def _update_game(self):
        fallen, spawned = self.board.collapse_and_fill()

        fallen_to_send: list[Tuple[int, int, int, int]] = []

        for elem, new_r, new_c in fallen:
            for lbl in self.tile_labels.values():
                if lbl.element is elem:
                    fallen_to_send.append((lbl.row, lbl.col, new_r, new_c))
                    break
        if not self.solo_game:
            if self.ctrl.mode == "chess":
                self.ctrl.auto_swap(fallen=fallen_to_send, spawned=spawned)

        for elem, new_r, new_c in fallen:
            for lbl in self.tile_labels.values():
                if lbl.element is elem:
                    print(f"elem {elem}")
                    print(f"lbl row {lbl.row}  lbl col {lbl.col}")
                    lbl.row, lbl.col = new_r, new_c
                    self.tile_labels.pop((elem.y, elem.x), None)  # до смены координат
                    self.tile_labels[(new_r, new_c)] = lbl
                    self._animate_fall(lbl, new_r)
                    audio.play_sound("falling")
                    break
        for elem in spawned:
            lbl = TileLabel(self, elem)
            pix = self._pix_for_elem(elem)
            lbl.setPixmap(pix)

            x = self.GRID_ORIGIN.x() + elem.y * self.CELL_SIZE
            y = self.GRID_ORIGIN.y() - elem.x * self.CELL_SIZE
            print(f"x {x} y {y}")
            lbl.setGeometry(x, y,
                            self.CELL_SIZE, self.CELL_SIZE)
            lbl.raise_()
            lbl.show()

            self.tile_labels[(elem.x, elem.y)] = lbl
            self._animate_fall(lbl, elem.x)
            audio.play_sound("falling")
        if not self.solo_game:
            if self.ctrl.mode == "time":
                self.ctrl.board = self.board
                self.ctrl.board_update_for_opp()

        while self.board.step():
            removed, bonuses = self.board.get_auto_matched()
            for r, c in removed:
                lbl = self.tile_labels.pop((r, c), None)
                if not lbl:
                    continue

                explosion = ExplosionLabel(self, lbl.element.color.value, lbl.pos(), self.CELL_SIZE, fps=100)

                lbl.deleteLater()

                explosion.raise_()
                explosion.show()
                audio.play_sound("removed")

            for r, c, bonus in bonuses:
                elem = self.board.cell(r, c)
                lbl = TileLabel(self, elem)
                pix = self._pix_for_elem(elem)
                lbl.setPixmap(pix)
                x = self.GRID_ORIGIN.x() + c * self.CELL_SIZE
                y = self.GRID_ORIGIN.y() + r * self.CELL_SIZE
                lbl.setGeometry(x, y, self.CELL_SIZE, self.CELL_SIZE)
                lbl.raise_()
                lbl.show()
                self.tile_labels[(r, c)] = lbl
                audio.play_sound("add_bonus")

            fallen, spawned = self.board.collapse_and_fill()
            fallen_to_send: list[Tuple[int, int, int, int]] = []

            for elem, new_r, new_c in fallen:
                for lbl in self.tile_labels.values():
                    if lbl.element is elem:
                        fallen_to_send.append((lbl.row, lbl.col, new_r, new_c))
                        break

            if not self.solo_game:
                if self.ctrl.mode == "chess":
                    self.ctrl.auto_swap_circle(fallen=fallen_to_send, spawned=spawned, bonuses=bonuses, removed=removed)

            for elem, new_r, new_c in fallen:
                for lbl in self.tile_labels.values():
                    if lbl.element is elem:
                        lbl.row, lbl.col = new_r, new_c
                        self.tile_labels.pop((elem.y, elem.x), None)  # до смены координат
                        self.tile_labels[(new_r, new_c)] = lbl
                        self._animate_fall(lbl, new_r)
                        audio.play_sound("falling")
                        break

            for elem in spawned:
                lbl = TileLabel(self, elem)
                pix = self._pix_for_elem(elem)
                lbl.setPixmap(pix)

                x = self.GRID_ORIGIN.x() + elem.y * self.CELL_SIZE
                y = self.GRID_ORIGIN.y() - elem.x * self.CELL_SIZE
                lbl.setGeometry(x, y,
                                self.CELL_SIZE, self.CELL_SIZE)
                lbl.raise_()
                lbl.show()

                self.tile_labels[(elem.x, elem.y)] = lbl
                self._animate_fall(lbl, elem.x)
                audio.play_sound("falling")
            if not self.solo_game:
                if self.ctrl.mode == "time":
                    self.ctrl.board = self.board
                    self.ctrl.board_update_for_opp()

    def _animate_swap(self, t1: TileLabel, t2: TileLabel, on_finished=None):
        group = QParallelAnimationGroup(self)
        for tile, end in ((t1, t2.pos()), (t2, t1.pos())):
            anim = QPropertyAnimation(tile, b'pos', self)
            anim.setDuration(150)
            anim.setEndValue(end)
            anim.setEasingCurve(QEasingCurve.InOutQuad)
            group.addAnimation(anim)

        self.pending_animations += 1

        def _after_anim():
            self._swap_tiles(t1, t2)
            if on_finished:
                on_finished()
            self.pending_animations -= 1
            self._check_animations_done()

        group.finished.connect(_after_anim)
        group.start()
        self.animations.append(group)
        # чистим уже закончившиеся
        self.animations = [g for g in self.animations if g.state() != QPropertyAnimation.Stopped]

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

    def render_from_board(self, first=False):
        for lbl in self.tile_labels.values():
            lbl.deleteLater()
        self.tile_labels.clear()

        for r in range(self.ROWS):
            for c in range(self.COLS):
                elem = self.board.cell(r, c)
                pix = self._pix_for_elem(elem)
                lbl = TileLabel(self, elem)
                audio.play_sound("falling", 1)
                lbl.setPixmap(pix)
                x = self.GRID_ORIGIN.x() + c * self.CELL_SIZE
                y = self.GRID_ORIGIN.y() + (-1 if first else r) * self.CELL_SIZE
                lbl.setGeometry(x, y, self.CELL_SIZE, self.CELL_SIZE)
                lbl.raise_()
                lbl.show()
                self.tile_labels[(r, c)] = lbl
                if first:
                    self._animate_fall(lbl, r)

    def _swap_tiles(self, tile1: TileLabel, tile2: TileLabel):
        r1, c1 = tile1.row, tile1.col
        r2, c2 = tile2.row, tile2.col

        tile1.row, tile1.col, tile2.row, tile2.col = r2, c2, r1, c1

        self.tile_labels.pop((r1, c1), None)
        self.tile_labels.pop((r2, c2), None)
        self.tile_labels[(tile1.row, tile1.col)] = tile1
        self.tile_labels[(tile2.row, tile2.col)] = tile2

    def _fire_rocket(self, r: int, c: int, orientation: Bonus):
        rocket_img = "rocket_h.png" if orientation == Bonus.ROCKET_H else "rocket_v.png"
        rocket_lbl = QLabel(self)
        pix = QPixmap(get_resource_path(f"assets/elements/{rocket_img}")) \
            .scaled(self.CELL_SIZE, self.CELL_SIZE)
        rocket_lbl.setPixmap(pix)
        start_x = self.GRID_ORIGIN.x() + c * self.CELL_SIZE
        start_y = self.GRID_ORIGIN.y() + r * self.CELL_SIZE
        rocket_lbl.setGeometry(start_x, start_y, self.CELL_SIZE, self.CELL_SIZE)
        rocket_lbl.show()
        rocket_lbl.raise_()

        anim = QPropertyAnimation(rocket_lbl, b"pos", self)
        anim.setDuration(100)
        anim.setEasingCurve(QEasingCurve.InQuad)
        if orientation == Bonus.ROCKET_H:
            end_x = self.GRID_ORIGIN.x()
            anim.setStartValue(QPoint(start_x, start_y))
            anim.setEndValue(QPoint(end_x, start_y))
        else:
            end_y = self.GRID_ORIGIN.y()
            audio.play_sound("rocket")
            anim.setStartValue(QPoint(start_x, start_y))
            anim.setEndValue(QPoint(start_x, end_y))

        def _on_rocket_done():
            rocket_lbl.deleteLater()

            explosion = ExplosionLabel(
                parent=self,
                color=Color.RED.value,
                pos=rocket_lbl.pos(),
                size=self.CELL_SIZE,
                fps=100,
                bonus=Bonus.NONE
            )

        anim.finished.connect(_on_rocket_done)
        anim.start()

    def _update_score(self, score: int):
        self.score += score
        if not self.solo_game:
            if self.ctrl.mode == "time":
                self.ctrl.score_update(self.score)
                if self.score > 999:
                    self.ctrl.finish(self.score)
                    self._clock_timer.stop()
                    self._show_waiting_overlay(f"Второй игрок еще не финишировал\n, ждём его…")
                    return
        self.display_number('score', self.score)

    def display_number(self, kind, value, color: str = None, x=None, y=None):
        value = 999 if value > 999 else value
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

    def _open_settings(self):
        if hasattr(self, "_settings") and self._settings.isVisible():
            return

        self._clock_timer.stop()

        self._settings = SettingsWindow(self)
        cx = self.x() + (self.width() - self._settings.width()) // 2
        cy = self.y() + (self.height() - self._settings.height()) // 2
        self._settings.move(cx, cy)
        self._settings.finished.connect(lambda _: self._clock_timer.start())
        self._settings.homeClicked.connect(self._on_settings_home)
        self._settings.show()

    def _tick_clock(self):
        self.elapsed_seconds += 1

        if not self.solo_game:
            if self.ctrl.mode == "time":
                self.ctrl.time_update(self.elapsed_seconds)
                if self.elapsed_seconds > self.ctrl.time:
                    self.ctrl.finish(self.score)
                    self._clock_timer.stop()
                    self._show_waiting_overlay(f"Второй игрок еще не финишировал\n, ждём его…")
                    return
        self.display_number('timer', self.elapsed_seconds)

    def _show_end_game(self, message: str, winner_name: str = "", score: int = 0):
        self.end_game_window = EndGameWindow(self, player_name=winner_name, message=message, score=score)
        self.end_game_window.exec_()
        self._clock_timer.stop()
        audio.switch_to_lobby()
        if self.main_window is not None:
            self.main_window.show()
        if not self.solo_game:
            self.ctrl.close_game()
        if self.opp_view:
            self.opp_view.close()
        self.close()

    def apply_state(self, command: str):
        logger.info(f"Обработка команды {command}")
        logger.info(f"Мой ход {self.ctrl.is_my_step}")
        if command == "start_game":
            self.board = self.ctrl.board
            self.render_from_board(first=True)

            if self.ctrl.mode == "time":
                self.opp_view = BoardView()
                self.opp_view.show()
                self.opp_view.update_board(self.board, True)
        elif command == "board":
            self.opp_view.update_board(self.ctrl.opp_board)
        elif command == "time":
            self.opp_view.tick_clock(self.ctrl.opp_time)
        elif command == "score":
            self.opp_view.update_score(self.ctrl.opp_score)
        elif command == "swap":
            self.ctrl.is_my_step = True
            a_row = self.ctrl.a_row
            a_col = self.ctrl.a_col
            b_row = self.ctrl.b_row
            b_col = self.ctrl.b_col
            logger.info(f"a_row {a_row} a_col {a_col}")
            logger.info(f"b_row {b_row} b_col {b_col}")
            success = self.ctrl.success
            removed = self.ctrl.removed
            bonuses = self.ctrl.bonuses
            a_tile = None
            b_tile = None
            for lbl in self.tile_labels.values():
                if lbl.row == a_row and lbl.col == a_col:
                    a_tile = lbl
                elif lbl.row == b_row and lbl.col == b_col:
                    b_tile = lbl
                if a_tile and b_tile:
                    break

            if a_tile and b_tile:
                self.handle_swap_request_my_swap(a_tile, b_tile, success=success, removed=removed, bonuses=bonuses)
            else:
                logger.warning(f"Не нашли соответствующие TileLabel для network step")
        elif command == "auto_swap":
            self.auto_swap()
        elif command == "auto_swap_circle":
            self.auto_swap_circle()
        elif command == "end_game":
            if self.waiting_overlay:
                self.waiting_overlay.close()
            self.setEnabled(True)
            self._show_end_game(message="С победой", winner_name=self.ctrl.winner_player, score=self.ctrl.winner_score)
        elif command == "error":
            self._clock_timer.stop()
            if self.ctrl.is_client:
                text = "Соединение с сервером потеряно."
            else:
                text = f"Игрок {self.ctrl.exit_nickname} отключился — игра прервана."
            QMessageBox.critical(self, "Ошибка", text)
            if self.main_window:
                self.main_window.show()
            self.ctrl.close_game()
            if self.opp_view:
                self.opp_view.close()
            if self.end_game_window:
                self.end_game_window.close()
            self.close()

    def handle_swap_request_my_swap(self, a_lbl: TileLabel, b_lbl: TileLabel, success: bool,
                                    removed: Set[Tuple[int, int]], bonuses: List[Tuple[int, int, Bonus]]):
        if abs(a_lbl.row - b_lbl.row) + abs(a_lbl.col - b_lbl.col) != 1:
            return
        audio.play_sound("swap")
        self._animate_swap(a_lbl, b_lbl,
                           lambda: self._after_swap_logic_my_swap(a_lbl, b_lbl, success=success, removed=removed,
                                                                  bonuses=bonuses))

    def _after_swap_logic_my_swap(self, a_lbl, b_lbl, success: bool, removed: Set[Tuple[int, int]],
                                  bonuses: List[Tuple[int, int, Bonus]]):
        if not success:
            self._animate_swap(a_lbl, b_lbl, on_finished=None)
            return

        audio.play_sound("nice_swap")
        if not bonuses and removed:
            self._update_score(len(removed))
            for r, c in removed:
                lbl = self.tile_labels.pop((r, c), None)
                if lbl and lbl.element.bonus in [Bonus.ROCKET_H, Bonus.ROCKET_V]:
                    self._fire_rocket(r, c, lbl.element.bonus)
                    lbl.deleteLater()
                elif lbl:
                    explosion = ExplosionLabel(self, lbl.element.color.value, lbl.pos(), self.CELL_SIZE, fps=100,
                                               bonus=lbl.element.bonus)

                    lbl.deleteLater()

                    explosion.raise_()
                    explosion.show()
                    if lbl.element.bonus == Bonus.BOMB:
                        audio.play_sound("boom")
                    else:
                        audio.play_sound("removed")

            self.ctrl.update_board()
            self.board = self.ctrl.board
            return

        self.ctrl.update_board()
        self.board = self.ctrl.board
        self._update_score(len(removed))
        for r, c in removed:
            lbl = self.tile_labels.pop((r, c), None)
            if not lbl:
                continue

            explosion = ExplosionLabel(self, lbl.element.color.value, lbl.pos(), self.CELL_SIZE, fps=100)

            lbl.deleteLater()

            explosion.raise_()
            explosion.show()
            audio.play_sound("removed")

        for bonus in bonuses:
            r = bonus["r"]
            c = bonus["c"]
            elem = self.board.cell(r, c)
            print(elem)
            lbl = TileLabel(self, elem)
            pix = self._pix_for_elem(elem)
            lbl.setPixmap(pix)
            x = self.GRID_ORIGIN.x() + c * self.CELL_SIZE
            y = self.GRID_ORIGIN.y() + r * self.CELL_SIZE
            lbl.setGeometry(x, y, self.CELL_SIZE, self.CELL_SIZE)
            lbl.raise_()
            lbl.show()
            self.tile_labels[(r, c)] = lbl
            audio.play_sound("add_bonus")

    def print_matrix(self):
        lines: List[str] = []
        for r in range(self.ROWS):
            row_chars: List[str] = []
            for c in range(self.COLS):
                lbl = self.tile_labels.get((r, c))
                if lbl and lbl.element and lbl.element.color:
                    char = lbl.element.color.name[0]
                else:
                    char = '.'
                row_chars.append(char)
            lines.append(' '.join(row_chars))
        print('\n'.join(lines))

    def auto_swap(self):
        self.ctrl.update_board()
        self.board = self.ctrl.board
        fallen, spawned = self.ctrl.fallen, self.ctrl.spawned
        print(f"fallen {fallen}")
        print("\n\n\n----------my board:-----------\n\n\n\n")
        print(self.board)
        print("\n\n\n----------self.tile_labels-----------\n\n\n\n")
        self.print_matrix()

        for old_r, old_c, new_r, new_c in fallen:
            lbl = self.tile_labels.pop((old_r, old_c), None)
            if not lbl:
                continue
            lbl.row, lbl.col = new_r, new_c
            self.tile_labels[(new_r, new_c)] = lbl
            self._animate_fall(lbl, new_r)
            audio.play_sound("falling")

        for elem in spawned:
            lbl = TileLabel(self, elem)
            pix = self._pix_for_elem(elem)
            lbl.setPixmap(pix)

            x = self.GRID_ORIGIN.x() + elem.y * self.CELL_SIZE
            y = self.GRID_ORIGIN.y() - elem.x * self.CELL_SIZE
            print(f"x {x} y {y}")
            lbl.setGeometry(x, y,
                            self.CELL_SIZE, self.CELL_SIZE)
            lbl.raise_()
            lbl.show()

            self.tile_labels[(elem.x, elem.y)] = lbl
            self._animate_fall(lbl, elem.x)
            audio.play_sound("falling")

        self.run_after_animations(lambda: self.render_from_board())

    def auto_swap_circle(self):
        self.ctrl.update_board()
        self.board = self.ctrl.board
        fallen, spawned = self.ctrl.fallen, self.ctrl.spawned
        removed = self.ctrl.removed
        bonuses = self.ctrl.bonuses

        for r, c in removed:
            lbl = self.tile_labels.pop((r, c), None)
            if not lbl:
                continue

            explosion = ExplosionLabel(self, lbl.element.color.value, lbl.pos(), self.CELL_SIZE, fps=100)

            lbl.deleteLater()

            explosion.raise_()
            explosion.show()
            audio.play_sound("removed")

        for r, c, bonus in bonuses:
            elem = self.board.cell(r, c)
            lbl = TileLabel(self, elem)
            pix = self._pix_for_elem(elem)
            lbl.setPixmap(pix)
            x = self.GRID_ORIGIN.x() + c * self.CELL_SIZE
            y = self.GRID_ORIGIN.y() + r * self.CELL_SIZE
            lbl.setGeometry(x, y, self.CELL_SIZE, self.CELL_SIZE)
            lbl.raise_()
            lbl.show()
            self.tile_labels[(r, c)] = lbl
            audio.play_sound("add_bonus")

        for old_r, old_c, new_r, new_c in fallen:
            lbl = self.tile_labels.pop((old_r, old_c), None)
            if not lbl:
                continue
            lbl.row, lbl.col = new_r, new_c
            self.tile_labels[(new_r, new_c)] = lbl
            self._animate_fall(lbl, new_r)
            audio.play_sound("falling")

        for elem in spawned:
            lbl = TileLabel(self, elem)
            pix = self._pix_for_elem(elem)
            lbl.setPixmap(pix)

            x = self.GRID_ORIGIN.x() + elem.y * self.CELL_SIZE
            y = self.GRID_ORIGIN.y() - elem.x * self.CELL_SIZE
            lbl.setGeometry(x, y,
                            self.CELL_SIZE, self.CELL_SIZE)
            lbl.raise_()
            lbl.show()

            self.tile_labels[(elem.x, elem.y)] = lbl
            self._animate_fall(lbl, elem.x)
            audio.play_sound("falling")

        self.run_after_animations(lambda: self.render_from_board())

    def closeEvent(self, event):
        if hasattr(self, "_settings") and self._settings.isVisible():
            self._settings.close()
            event.ignore()
            return

        super().closeEvent(event)

    def _show_waiting_overlay(self, text: str):
        if self.waiting_overlay is None:
            self.waiting_overlay = QLabel(text, self)
            self.waiting_overlay.setAlignment(Qt.AlignCenter)
            self.waiting_overlay.setStyleSheet(
                'background: rgba(0,0,0,0.5); color: white; font-size: 24px;'
            )
            self.waiting_overlay.setGeometry(0, 0, self.width(), self.height())
        self.waiting_overlay.show()
        self.setEnabled(False)

    def _check_animations_done(self):
        if self.pending_animations == 0 and self._on_all_animations:
            cb = self._on_all_animations
            self._on_all_animations = None
            cb()

    def run_after_animations(self, callback):
        if self.pending_animations > 0:
            self._on_all_animations = callback
        else:
            callback()

    def _on_settings_home(self):
        self._clock_timer.stop()
        if self.main_window:
            self.main_window.show()
        self.ctrl.close_game()
        if self.opp_view:
            self.opp_view.close()
        if self.end_game_window:
            self.end_game_window.close()
        self.close()
