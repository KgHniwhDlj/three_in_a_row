from enum import Enum, auto


class Color(Enum):
    ORANGE = "orange"
    PURPLE = "purple"
    RED = "red"
    YELLOW = "yellow"


class Bonus(Enum):
    NONE = auto()
    ROCKET_H = auto()
    ROCKET_V = auto()
    BOMB = auto()
