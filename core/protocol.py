import json
from typing import Dict, List, Tuple, Any, Set, Union

from core.element import Element
from core.enums import Bonus


def _elem_to_dict(e: Element) -> Dict[str, Any]:
    return {"x": e.x, "y": e.y,
            "color": e.color.value,
            "bonus": e.bonus.name,
            "img": e.img}


def _dict_to_elem(d: Dict[str, Any]) -> Element:
    from core.enums import Color, Bonus
    e = Element(d["x"], d["y"], Color(d["color"]), Bonus[d["bonus"]])
    return e


def dumps(msg: Dict[str, Any]) -> bytes:
    return json.dumps(msg, ensure_ascii=False).encode()


def loads(raw: bytes) -> Dict[str, Any]:
    return json.loads(raw.decode())


def start_game(
        mode: str,
        queue: List[str],
        nicknames: List[str],
        board: List[List[str]],
        time_limit: int
) -> Dict[str, Any]:
    return {
        "command": "start_game",
        "mode": mode,
        "queue_players": queue,
        "current_player": queue[0],
        "nicknames": nicknames,
        "board": board,
        "time_limit": time_limit
    }


def swap(
        a_lbl: Tuple[int, int],
        b_lbl: Tuple[int, int],
        next_player: str,
        removed: Set[Tuple[int, int]],
        bonuses: List[Tuple[int, int, Bonus]],
        success: bool,
        board: List[List[str]]
) -> Dict[str, Any]:
    a_row, a_col = a_lbl
    b_row, b_col = b_lbl
    return {
        "command": "swap",
        "a_row": a_row,
        "a_col": a_col,
        "b_row": b_row,
        "b_col": b_col,
        "next_player": next_player,
        "board": board,
        "success": success,
        "removed": [[r, c] for (r, c) in sorted(removed)],
        "bonuses": [
            {"r": r, "c": c, "bonus": bonus.name}
            for (r, c, bonus) in bonuses
        ]
    }


def auto_swap(
        fallen: List[Tuple[int, int, int, int]],
        spawned: List[Element],
        board: List[List[str]]
) -> Dict[str, Any]:
    return {
        "command": "auto_swap",
        "fallen": [
            {"old_r": o_r, "old_c": o_c, "new_r": n_r, "new_c": n_c}
            for o_r, o_c, n_r, n_c in fallen
        ],
        "spawned": [
            _elem_to_dict(e) for e in spawned
        ],
        "board": board,
    }


def board(board_: List[List[str]]) -> Dict[str, Any]:
    return {
        "command": "board",
        "board": board_,
    }


def score(score_: int) -> Dict[str, Any]:
    return {
        "command": "score",
        "score": score_,
    }


def time(time_: int) -> Dict[str, Any]:
    return {
        "command": "time",
        "time": time_,
    }


def auto_swap_circle(
        fallen: List[Tuple[int, int, int, int]],
        spawned: List[Element],
        removed: Set[Tuple[int, int]],
        bonuses: List[Tuple[int, int, Bonus]],
        board_: List[List[str]]
) -> Dict[str, Any]:
    return {
        "command": "auto_swap_circle",
        "fallen": [
            {"old_r": o_r, "old_c": o_c, "new_r": n_r, "new_c": n_c}
            for o_r, o_c, n_r, n_c in fallen
        ],
        "removed": [[r, c] for (r, c) in sorted(removed)],
        "spawned": [
            _elem_to_dict(e) for e in spawned
        ],
        "bonuses": [
            {"r": r, "c": c, "bonus": bonus.name}
            for (r, c, bonus) in bonuses
        ],
        "board": board_,
    }


def end_game(winner: str, score_: int) -> Dict:
    return {"command": "end_game", "winner": winner, "score": score_}


def finish(score_: int) -> Dict:
    return {"command": "finish", "score": score_}
