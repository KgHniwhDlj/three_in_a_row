# core/board.py
from __future__ import annotations
import random
from typing import List, Tuple, Dict, Iterable, Set

from core.enums import Color, Bonus
from core.element import Element
from logger import logger


class Board:
    ROWS, COLS = 8, 7
    COLORS = list(Color)

    def __init__(self):
        self.grid: List[List[Element | None]] = [
            [None] * self.COLS for _ in range(self.ROWS)
        ]
        self._fill_start_board()

    def cell(self, r: int, c: int) -> Element | None:
        return self.grid[r][c]

    def swap(self,
             a: Tuple[int, int],
             b: Tuple[int, int]
             ) -> Tuple[bool, Set[Tuple[int, int]], List[Tuple[int, int, Bonus]]]:
        r1, c1 = a
        r2, c2 = b
        self.grid[r1][c1], self.grid[r2][c2] = self.grid[r2][c2], self.grid[r1][c1]
        e1 = self.grid[r1][c1]
        e2 = self.grid[r2][c2]
        e1.x, e1.y = c1, r1
        e2.x, e2.y = c2, r2
        if e1.bonus != Bonus.NONE:
            logger.info(f"{e1} bonus activated")
            removed = self._trigger_bonus((e1.y, e1.x))
            return True, removed, []

        if e2.bonus != Bonus.NONE:
            logger.info(f"{e2} bonus activated")
            removed = self._trigger_bonus((e2.y, e2.x))
            return True, removed, []

        if not self._any_matches_after({a, b}):
            # откат
            self.grid[r1][c1], self.grid[r2][c2] = self.grid[r2][c2], self.grid[r1][c1]
            return False, set(), []

        matched = self._collect_matches()
        bonus_cells = self._create_bonuses(matched, a, b)
        to_remove = matched - set((r, c) for r, c, _ in bonus_cells)
        for r, c in to_remove:
            self.grid[r][c] = None

        return True, matched, bonus_cells

    def _create_bonuses(self,
                        matched: Set[Tuple[int, int]],
                        a: Tuple[int, int],
                        b: Tuple[int, int]
                        ) -> List[Tuple[int, int, Bonus]]:
        bonuses = []
        used = set()

        def make_bonus(run: List[Tuple[int, int]]):
            size = len(run)
            if size < 4:
                return
            target = next((cell for cell in (a, b) if cell in run), None)
            if target is None:
                target = run[size // 2]
            r, c = target
            base = self.grid[r][c]
            col = base.color
            if size == 4:
                bonus = random.choice([Bonus.ROCKET_H, Bonus.ROCKET_V])
            else:
                bonus = Bonus.BOMB
            self.grid[r][c] = Element(r, c, col, bonus)
            bonuses.append((r, c, bonus))
            used.update(run)

        for r in range(self.ROWS):
            run: List[Tuple[int, int]] = []
            prev_color = None
            for c in range(self.COLS):
                cell = (r, c)
                elem = self.grid[r][c]
                if elem and (prev_color is None or elem.color == prev_color):
                    run.append(cell)
                else:
                    make_bonus(run)
                    run = [cell]
                prev_color = elem.color if elem else None
            make_bonus(run)

        for c in range(self.COLS):
            run = []
            prev_color = None
            for r in range(self.ROWS):
                cell = (r, c)
                elem = self.grid[r][c]
                if elem and (prev_color is None or elem.color == prev_color):
                    run.append(cell)
                else:
                    make_bonus(run)
                    run = [cell]
                prev_color = elem.color if elem else None
            make_bonus(run)

        return bonuses

    def has_move(self) -> bool:
        for r in range(self.ROWS):
            for c in range(self.COLS):
                if c + 1 < self.COLS and self._will_match((r, c), (r, c + 1)):
                    return True
                if r + 1 < self.ROWS and self._will_match((r, c), (r + 1, c)):
                    return True
        return False

    def _fill_start_board(self):
        while True:
            for r in range(self.ROWS):
                for c in range(self.COLS):
                    self.grid[r][c] = Element(r, c, random.choice(self.COLORS))
            if not self._collect_matches() and self.has_move():
                break

    def _any_matches_after(self, cells: Iterable[Tuple[int, int]]) -> bool:
        for r, c in cells:
            if self._line_length(r, c, 0, 1) >= 3 or self._line_length(r, c, 1, 0) >= 3:
                return True
        return False

    def _line_length(self, r, c, dr, dc) -> int:
        start = self.grid[r][c]
        if start is None:
            return 0
        color = start.color
        cnt = 1
        i, j = r + dr, c + dc
        while 0 <= i < self.ROWS and 0 <= j < self.COLS and self.grid[i][j] and self.grid[i][j].color == color:
            cnt += 1
            i += dr
            j += dc
        i, j = r - dr, c - dc
        while 0 <= i < self.ROWS and 0 <= j < self.COLS and self.grid[i][j] and self.grid[i][j].color == color:
            cnt += 1
            i -= dr
            j -= dc
        return cnt

    def _collect_matches(self) -> set[tuple[int, int]]:
        matches = set()
        for r in range(self.ROWS):
            run = []
            for c in range(self.COLS):
                cur = self.grid[r][c]
                if not run or (cur and run[-1] and cur.color == run[-1].color):
                    run.append(cur)
                else:
                    if len(run) >= 3:
                        matches.update({(r, x) for x in range(c - len(run), c)})
                    run = [cur]
            if len(run) >= 3:
                matches.update({(r, x) for x in range(self.COLS - len(run), self.COLS)})

        for c in range(self.COLS):
            run = []
            for r in range(self.ROWS):
                cur = self.grid[r][c]
                if not run or (cur and run[-1] and cur.color == run[-1].color):
                    run.append(cur)
                else:
                    if len(run) >= 3:
                        matches.update({(y, c) for y in range(r - len(run), r)})
                    run = [cur]
            if len(run) >= 3:
                matches.update({(y, c) for y in range(self.ROWS - len(run), self.ROWS)})

        return matches

    def _trigger_bonus(self, cell: Tuple[int, int]) -> Set[Tuple[int, int]]:
        r, c = cell
        elem = self.grid[r][c]
        removed = set()

        if elem.bonus == Bonus.BOMB:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < self.ROWS and 0 <= cc < self.COLS:
                        removed.add((rr, cc))

        elif elem.bonus == Bonus.ROCKET_H:
            removed = {(r, cc) for cc in range(0, c)}

        elif elem.bonus == Bonus.ROCKET_V:
            removed = {(rr, c) for rr in range(0, r)}

        removed.add((r, c))
        for rr, cc in removed:
            self.grid[rr][cc] = None

        return removed

    def collapse_and_fill(self) -> tuple[list[tuple[Element, int, int]], list[Element]]:
        fallen: list[tuple[Element, int, int]] = []

        for c in range(self.COLS):
            write = self.ROWS - 1
            for read in range(self.ROWS - 1, -1, -1):
                e = self.grid[read][c]
                if e is not None:
                    if read != write:
                        self.grid[write][c] = e
                        self.grid[read][c] = None
                        e.y, e.x = write, c
                        fallen.append((e, write, c))
                    write -= 1

        spawned: list[Element] = []
        for c in range(self.COLS):
            for r in range(self.ROWS):
                if self.grid[r][c] is None:
                    new = Element(r, c, random.choice(self.COLORS))
                    self.grid[r][c] = new
                    spawned.append(new)

        if not self.has_move():
            e = random.choice([e for row in self.grid for e in row])
            e.color = random.choice([c for c in self.COLORS if c != e.color])
        return fallen, spawned

    def _will_match(self, a, b) -> bool:
        (r1, c1), (r2, c2) = a, b
        g = self.grid
        g[r1][c1], g[r2][c2] = g[r2][c2], g[r1][c1]
        ok = self._any_matches_after({a, b})
        g[r1][c1], g[r2][c2] = g[r2][c2], g[r1][c1]
        return ok

    def __str__(self):
        rows = []
        for row in self.grid:
            row_str = ' '
            for elem in row:
                if elem is None:
                    row_str += '.'
                else:
                    symbol = elem.color.value[0]
                    if elem.bonus:
                        if elem.bonus == Bonus.ROCKET_H:
                            symbol = 'h'
                        elif elem.bonus == Bonus.ROCKET_V:
                            symbol = 'v'
                        elif elem.bonus == Bonus.BOMB:
                            symbol = 'B'
                    row_str += symbol
            rows.append(row_str)
        return '\n'.join(rows)

    def step(self):
        matched = self._collect_matches()
        return True if len(matched) >= 1 else False

    def get_auto_matched(self) -> Tuple[Set[Tuple[int, int]], List[Tuple[int, int, Bonus]]]:
        matched = self._collect_matches()
        bonus_cells = self._create_bonuses_auto(matched)
        to_remove = matched - set((r, c) for r, c, _ in bonus_cells)
        for r, c in to_remove:
            self.grid[r][c] = None

        return matched, bonus_cells

    def _create_bonuses_auto(self, matched: Set[Tuple[int, int]]
                             ) -> List[Tuple[int, int, Bonus]]:
        bonuses: List[Tuple[int, int, Bonus]] = []

        def place_bonus(run: List[Tuple[int, int]]):
            n = len(run)
            if n < 4:
                return
            r, c = random.choice(run)
            base = self.grid[r][c]
            if n == 4:
                bonus = random.choice([Bonus.ROCKET_H, Bonus.ROCKET_V])
            else:  # n ≥ 5
                bonus = Bonus.BOMB
            self.grid[r][c] = Element(r, c, base.color, bonus)
            bonuses.append((r, c, bonus))

        # горизонтальные последовательности
        for r in range(self.ROWS):
            run = []
            for c in range(self.COLS):
                if (r, c) in matched:
                    if not run or self.grid[r][c].color == self.grid[r][run[-1]].color:
                        run.append(c)
                    else:
                        place_bonus([(r, x) for x in run])
                        run = [c]
                else:
                    place_bonus([(r, x) for x in run])
                    run = []
            place_bonus([(r, x) for x in run])

        for c in range(self.COLS):
            run = []
            for r in range(self.ROWS):
                if (r, c) in matched:
                    if not run or self.grid[r][c].color == self.grid[run[-1]][c].color:
                        run.append(r)
                    else:
                        place_bonus([(x, c) for x in run])
                        run = [r]
                else:
                    place_bonus([(x, c) for x in run])
                    run = []
            place_bonus([(x, c) for x in run])

        self._last_auto_bonuses = bonuses  # запоминаем для get_auto_matched
        return bonuses

    def board_from_matrix(self, mat: list[list[str]]):
        for r, row in enumerate(mat):
            for c, ch in enumerate(row):
                # ch: 'r','o','h','v','B','.'
                if ch == '.':
                    self.grid[r][c] = None
                else:
                    ch_low = ch.lower()
                    color_map = {'r': Color.RED, 'o': Color.ORANGE, 'p': Color.PURPLE, 'y': Color.YELLOW,
                                 'h': Color.RED, 'v': Color.ORANGE, 'b': Color.PURPLE}
                    bonus_map = {'h': Bonus.ROCKET_H, 'v': Bonus.ROCKET_V, 'b': Bonus.BOMB}

                    color = color_map[ch_low]
                    bonus = bonus_map.get(ch_low, Bonus.NONE)
                    self.grid[r][c] = Element(r, c, color, bonus)

    def to_matrix(self) -> list[list[str]]:
        matrix: list[list[str]] = []
        for row in self.grid:
            row_chars: list[str] = []
            for elem in row:
                if elem is None:
                    row_chars.append('.')
                else:
                    row_chars.append(elem.short())
            matrix.append(row_chars)
        return matrix
