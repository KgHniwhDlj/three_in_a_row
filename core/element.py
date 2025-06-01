from __future__ import annotations

from dataclasses import dataclass, field

from core.enums import Color, Bonus


@dataclass
class Element:
    x: int
    y: int
    color: Color
    bonus: Bonus = Bonus.NONE
    img: str = field(init=False)

    def __post_init__(self):
        root = "assets/elements"
        if self.bonus == Bonus.NONE:
            self.img = f"{root}/{self.color.value}.png"
        elif self.bonus == Bonus.BOMB:
            self.img = f"{root}/bomb.png"
        elif self.bonus in (Bonus.ROCKET_H, Bonus.ROCKET_V):
            axis = "h" if self.bonus == Bonus.ROCKET_H else "v"
            self.img = f"{root}/rocket_{axis}.png"

    def short(self) -> str:
        char = self.color.value[0].upper()
        if self.bonus == Bonus.NONE:
            return char
        if self.bonus == Bonus.BOMB:
            return "B"
        return "H" if self.bonus == Bonus.ROCKET_H else "V"