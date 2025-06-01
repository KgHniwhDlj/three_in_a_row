from __future__ import annotations

import random
from typing import Callable
from typing import Set, List, Tuple

from core import protocol as proto
from core.board import Board
from core.element import Element
from core.enums import Color, Bonus
from logger import logger


class GameController:
    def __init__(self,
                 mode: str,
                 time: int,
                 nickname: str,
                 is_client: bool = True,
                 on_send: Callable[[bytes], None] | None = None,
                 on_close: Callable[[], None] | None = None):
        self.is_opp_finish = False
        self.winner_score = None
        self.my_score = None
        self.b_col = None
        self.b_row = None
        self.a_col = None
        self.a_row = None
        self.swap_occurred = False
        self.new_board = None
        self.success = None
        self.bonuses = None
        self.removed = None
        self.spawned = None
        self.fallen = None
        self.exit_nickname = None
        self.mode = mode
        self.time = time
        self.opp_time = 1
        self.opp_score = 0
        self.opp_board = None
        self.nicknames = None
        self._send = on_send
        self._close_net = on_close
        self.state_ready: Callable[[str], None] | None = None
        self.winner_player = None
        self.step_player = None
        self.my_nickname = nickname
        self.is_client = is_client
        self.value_player = 2
        self.queue = []
        self.board = None
        self.elapsed_seconds = 0
        self.score = 0
        self.is_my_step = False
        self.current = ""

    def _dispatch(self, cmd: str) -> None:
        if self.state_ready:
            self.state_ready(cmd)

    def new_game(self, nicknames):
        self.nicknames = nicknames
        self.current = self.my_nickname
        self.board = Board()

        self.queue = nicknames[:]
        random.shuffle(self.queue)
        self.current = self.queue[0]
        self.is_my_step = self.my_nickname == self.current

        msg = proto.start_game(
            mode=self.mode,
            queue=self.queue,
            nicknames=self.nicknames,
            board=self.board.to_matrix(),
            time_limit=self.time
        )

        if self._send:
            self._send(proto.dumps(msg))

        self._dispatch("start_game")

    def _next_player(self):
        idx = (self.queue.index(self.current) + 1) % len(self.queue)
        return self.queue[idx]

    def swap(self, a_lbl: Tuple[int, int], b_lbl: Tuple[int, int], success: bool, removed: Set[Tuple[int, int]],
             bonuses: List[Tuple[int, int, Bonus]]):
        self.current = self.my_nickname
        self.current = self._next_player()
        self.is_my_step = self.my_nickname == self.current
        if self.mode == "time":
            self.is_my_step = True
        if self._send:
            self._send(proto.dumps(proto.swap(a_lbl=a_lbl, b_lbl=b_lbl, next_player=self.current,
                                              success=success, removed=removed, bonuses=bonuses,
                                              board=self.board.to_matrix())))

    def auto_swap(self, fallen: list[tuple[int, int, int, int]], spawned: list[Element]):
        if self.mode == "time":
            self.is_my_step = True
        if self._send:
            self._send(proto.dumps(proto.auto_swap(fallen=fallen, spawned=spawned,
                                                   board=self.board.to_matrix())))

    def auto_swap_circle(self, fallen: list[Tuple[int, int, int, int]],
                         spawned: List[Element],
                         removed: Set[Tuple[int, int]],
                         bonuses: List[Tuple[int, int, Bonus]]):
        if self.mode == "time":
            self.is_my_step = True
        if self._send:
            self._send(proto.dumps(proto.auto_swap_circle(fallen=fallen, spawned=spawned,
                                                          board_=self.board.to_matrix(), bonuses=bonuses, removed=removed)))

    def handle_command(self, data):
        if data["command"] == "start_game":
            self.handle_start_game(data)
            return True
        elif data["command"] == "swap":
            self.handle_swap(data)
        elif data["command"] == "auto_swap":
            self.handle_auto_swap(data)
        elif data["command"] == "end_game":
            self.end_game(data)
        elif data["command"] == "score":
            self.handle_score(data)
        elif data["command"] == "board":
            self.handle_board(data)
        elif data["command"] == "time":
            self.handle_time(data)
        elif data["command"] == "finish":
            self.handle_finish(data)
        elif data["command"] == "auto_swap_circle":
            self.handle_auto_swap_circle(data)
        elif data["command"] == "end_game":
            self.end_game(data)

    def handle_start_game(self, data):
        self.queue = data.get("queue_players")
        self.current = data.get("current_player")
        self.is_my_step = self.my_nickname == self.current
        self.board = Board()
        self.time = data.get("time_limit")
        self.board.board_from_matrix(data.get("board"))
        self.nicknames = data.get("nicknames")
        self.mode = data.get("mode")

    def handle_auto_swap(self, data):
        self.fallen = [
            (f["old_r"], f["old_c"], f["new_r"], f["new_c"])
            for f in data["fallen"]
        ]
        self.spawned = [
            Element(d["x"], d["y"], Color(d["color"]), Bonus[d["bonus"]])
            for d in data["spawned"]
        ]
        self.is_my_step = self.my_nickname == self.current
        if self.mode == "time":
            self.is_my_step = True
        self.new_board = data.get("board")
        self.current = data.get("next_player")
        self._dispatch("auto_swap")

    def handle_auto_swap_circle(self, data):
        self.fallen = [
            (f["old_r"], f["old_c"], f["new_r"], f["new_c"])
            for f in data["fallen"]
        ]
        self.spawned = [
            Element(d["x"], d["y"], Color(d["color"]), Bonus[d["bonus"]])
            for d in data["spawned"]
        ]
        self.new_board = data.get("board")
        self.bonuses = data.get("bonuses")
        self.is_my_step = self.my_nickname == self.current
        if self.mode == "time":
            self.is_my_step = True
        self._dispatch("auto_swap")

    def handle_swap(self, data):
        self.a_row = data.get("a_row")
        self.a_col = data.get("a_col")
        self.b_row = data.get("b_row")
        self.b_col = data.get("b_col")
        self.current = data.get("next_player")
        self.is_my_step = self.my_nickname == self.current
        if self.mode == "time":
            self.is_my_step = True

        self.removed = data.get("removed")
        self.bonuses = data.get("bonuses")
        self.success = data.get("success")
        self.new_board = data.get("board")
        self.swap_occurred = True
        self._dispatch("swap")

    def end_game(self, data):
        self.winner_player = data.get("winner")
        self.winner_score = data.get("score")
        self._dispatch("end_game")

    def _compute_and_end_game(self):
        if self.opp_score > self.my_score:
            winner, winning_score = self.opponent_nickname, self.opp_score
        else:
            winner, winning_score = self.my_nickname, self.my_score
        if self._send:
            self._send(proto.dumps(proto.end_game(winner=winner, score_=winning_score)))
        self.end_game(proto.end_game(winner=winner, score_=winning_score))

    def close_game(self):
        if self._close_net:
            self._close_net()

    def handle_error(self, nickname: str | None = None):
        self.exit_nickname = nickname
        self._dispatch("error")

    def update_board(self):
        if self.swap_occurred:
            self.swap_occurred = False
            self.board.board_from_matrix(self.new_board)

    def time_update(self, time: int):
        if self._send:
            self._send(proto.dumps(proto.time(time_=time)))

    def handle_time(self, data):
        self.opp_time = data.get("time")
        self._dispatch("time")

    def score_update(self, score: int):
        print("update score")
        if self._send:
            self._send(proto.dumps(proto.score(score_=score)))

    def handle_score(self, data):
        self.opp_score = data.get("score")
        self._dispatch("score")

    def board_update_for_opp(self):
        if self._send:
            self._send(proto.dumps(proto.board(board_=self.board.to_matrix())))

    def handle_board(self, data):
        self.opp_board = Board()
        self.opp_board.board_from_matrix(data.get("board"))
        self._dispatch("board")

    @property
    def opponent_nickname(self) -> str | None:
        for nick in self.nicknames:
            if nick != self.my_nickname:
                return nick
        return None

    def finish(self, score: int):
        self.my_score = score
        if self.is_opp_finish:
            self._compute_and_end_game()
        else:
            if self._send:
                self._send(proto.dumps(proto.finish(score_=score)))

    def handle_finish(self, data):
        self.is_opp_finish = True
        self.opp_score = data.get("score")
