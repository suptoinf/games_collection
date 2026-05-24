"""
数独 (Sudoku) — 经典 9×9
"""

import tkinter as tk
import copy
import random
from typing import Optional

# 预置数独题库（按难度分组，0 表示空格）
_PUZZLES: dict[str, list[list[int]]] = {
    '简单': [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9],
    ],
    '中等': [
        [0, 0, 0, 2, 6, 0, 7, 0, 1],
        [6, 8, 0, 0, 7, 0, 0, 9, 0],
        [1, 9, 0, 0, 0, 4, 5, 0, 0],
        [8, 2, 0, 1, 0, 0, 0, 4, 0],
        [0, 0, 4, 6, 0, 2, 9, 0, 0],
        [0, 5, 0, 0, 0, 3, 0, 2, 8],
        [0, 0, 9, 3, 0, 0, 0, 7, 4],
        [0, 4, 0, 0, 5, 0, 0, 3, 6],
        [7, 0, 3, 0, 1, 8, 0, 0, 0],
    ],
    '困难': [
        [0, 2, 0, 6, 0, 8, 0, 0, 0],
        [5, 8, 0, 0, 0, 9, 7, 0, 0],
        [0, 0, 0, 0, 4, 0, 0, 0, 0],
        [3, 7, 0, 0, 0, 0, 5, 0, 0],
        [6, 0, 0, 0, 0, 0, 0, 0, 4],
        [0, 0, 8, 0, 0, 0, 0, 1, 3],
        [0, 0, 0, 0, 2, 0, 0, 0, 0],
        [0, 0, 9, 8, 0, 0, 0, 3, 6],
        [0, 0, 0, 3, 0, 6, 0, 9, 0],
    ],
}

_DIFFICULTIES = ['简单', '中等', '困难']


class Sudoku(tk.Frame):
    """数独游戏"""

    SIZE = 9
    CELL_SIZE = 46
    GRID_SIZE = SIZE * CELL_SIZE
    FONT = ('Segoe UI', 18, 'bold')
    FONT_SMALL = ('Segoe UI', 10)

    def __init__(self, parent):
        super().__init__(parent, bg='#1a1a1a')

        self._difficulty = '简单'
        self._board: list[list[int]] = []      # 当前完整棋盘
        self._solution: list[list[int]] = []    # 完整解（目前没用，可做提示）
        self._given: list[list[bool]] = []      # True = 预置不可改
        self._selected: Optional[tuple[int, int]] = None  # (r, c)
        self._conflicts: set[tuple[int, int]] = set()
        self._game_won = False

        self._setup_ui()
        self._load_puzzle('简单')

    # ── UI ──

    def _setup_ui(self):
        header = tk.Frame(self, bg='#1a1a1a')
        header.pack(fill=tk.X, padx=10, pady=(8, 4))

        tk.Label(header, text='🧩 数独',
                 fg='#e0e0e0', bg='#1a1a1a',
                 font=('Segoe UI', 14, 'bold')).pack(side=tk.LEFT)

        btn_style = {'bg': '#3a3a3a', 'fg': 'white', 'relief': tk.FLAT,
                     'font': ('Segoe UI', 10), 'padx': 10, 'pady': 2,
                     'cursor': 'hand2', 'activebackground': '#4a4a4a'}

        # 难度选择按钮
        self._diff_buttons: dict[str, tk.Button] = {}
        for diff in _DIFFICULTIES:
            btn = tk.Button(
                header, text=diff, **btn_style,
                command=lambda d=diff: self._load_puzzle(d))
            btn.pack(side=tk.LEFT, padx=2)
            self._diff_buttons[diff] = btn

        hint_btn = tk.Button(header, text='💡 提示', **btn_style,
                             command=self._give_hint)
        hint_btn.pack(side=tk.RIGHT, padx=2)

        # 选数字按钮 (1-9)
        num_bar = tk.Frame(self, bg='#1a1a1a')
        num_bar.pack(fill=tk.X, padx=10, pady=(0, 6))

        for n in range(1, 10):
            btn = tk.Button(num_bar, text=str(n),
                            bg='#2a2a2a', fg='#e0e0e0',
                            relief=tk.RAISED, bd=1,
                            font=('Segoe UI', 11, 'bold'),
                            width=2, cursor='hand2',
                            activebackground='#4a4a4a',
                            command=lambda v=n: self._place_number(v))
            btn.pack(side=tk.LEFT, padx=2)

        clear_btn = tk.Button(num_bar, text='✕', bg='#3a2a2a', fg='#e0e0e0',
                              relief=tk.RAISED, bd=1,
                              font=('Segoe UI', 11, 'bold'),
                              width=2, cursor='hand2',
                              activebackground='#5a3a3a',
                              command=lambda: self._place_number(0))
        clear_btn.pack(side=tk.LEFT, padx=2)

        # 画布
        self._canvas = tk.Canvas(self, width=self.GRID_SIZE, height=self.GRID_SIZE,
                                 bg='#2a2a2a', highlightthickness=0)
        self._canvas.pack(pady=(4, 10))
        self._canvas.bind('<Button-1>', self._on_click)
        self._canvas.bind('<Key>', self._on_key)  # 键盘输入
        self._canvas.focus_set()

    def _load_puzzle(self, difficulty: str):
        """加载指定难度的题目"""
        puzzle = copy.deepcopy(_PUZZLES[difficulty])
        self._difficulty = difficulty
        self._board = puzzle
        self._solution = self._solve(copy.deepcopy(puzzle))
        self._given = [[puzzle[r][c] != 0 for c in range(self.SIZE)]
                       for r in range(self.SIZE)]
        self._selected = None
        self._conflicts.clear()
        self._game_won = False

        # 高亮当前难度按钮
        for diff, btn in self._diff_buttons.items():
            btn.config(bg='#5a7a5a' if diff == difficulty else '#3a3a3a')

        self._draw()

    def _give_hint(self):
        """在选中格子填入正确答案"""
        if self._selected is None or not self._solution:
            return
        r, c = self._selected
        if self._given[r][c] or self._game_won:
            return
        self._board[r][c] = self._solution[r][c]
        self._check_conflicts()
        self._draw()
        self._check_win()

    # ── 事件 ──

    def _on_click(self, event):
        self._canvas.focus_set()
        c = event.x // self.CELL_SIZE
        r = event.y // self.CELL_SIZE
        if 0 <= r < self.SIZE and 0 <= c < self.SIZE:
            self._selected = (r, c)
            self._draw()

    def _on_key(self, event):
        if self._selected is None or self._game_won:
            return
        r, c = self._selected
        if self._given[r][c]:
            return

        if event.char in '123456789':
            self._board[r][c] = int(event.char)
        elif event.keysym in ('BackSpace', 'Delete') or event.char == '\x08':
            self._board[r][c] = 0
        else:
            return

        self._check_conflicts()
        self._draw()
        self._check_win()

    def _place_number(self, num: int):
        """通过数字按钮放置数字"""
        if self._selected is None or self._game_won:
            return
        r, c = self._selected
        if self._given[r][c]:
            return
        self._board[r][c] = num
        self._check_conflicts()
        self._draw()
        self._check_win()

    # ── 冲突检测 ──

    def _check_conflicts(self):
        """检查当前棋盘所有冲突"""
        self._conflicts.clear()

        def _add_conflict(r, c):
            if not self._given[r][c] and self._board[r][c] != 0:
                self._conflicts.add((r, c))

        # 行
        for r in range(self.SIZE):
            seen = {}
            for c in range(self.SIZE):
                v = self._board[r][c]
                if v != 0:
                    if v in seen:
                        _add_conflict(r, c)
                        _add_conflict(seen[v][0], seen[v][1])
                    else:
                        seen[v] = (r, c)

        # 列
        for c in range(self.SIZE):
            seen = {}
            for r in range(self.SIZE):
                v = self._board[r][c]
                if v != 0:
                    if v in seen:
                        _add_conflict(r, c)
                        _add_conflict(seen[v][0], seen[v][1])
                    else:
                        seen[v] = (r, c)

        # 宫 (3x3)
        for br in range(3):
            for bc in range(3):
                seen = {}
                for dr in range(3):
                    for dc in range(3):
                        r, c = br * 3 + dr, bc * 3 + dc
                        v = self._board[r][c]
                        if v != 0:
                            if v in seen:
                                _add_conflict(r, c)
                                _add_conflict(seen[v][0], seen[v][1])
                            else:
                                seen[v] = (r, c)

    def _check_win(self):
        """检查胜利：所有格子填满且无冲突"""
        if self._conflicts:
            return
        for r in range(self.SIZE):
            for c in range(self.SIZE):
                if self._board[r][c] == 0:
                    return
        self._game_won = True
        self._draw_win_overlay()

    # ── 求解器（用于生成提示/解） ──

    def _solve(self, board) -> Optional[list[list[int]]]:
        """简单回溯求解器"""
        empty = self._find_empty(board)
        if not empty:
            return board  # 已解完
        r, c = empty
        for num in range(1, 10):
            if self._is_valid(board, r, c, num):
                board[r][c] = num
                result = self._solve(board)
                if result:
                    return result
                board[r][c] = 0
        return None

    def _find_empty(self, board):
        for r in range(self.SIZE):
            for c in range(self.SIZE):
                if board[r][c] == 0:
                    return (r, c)
        return None

    def _is_valid(self, board, row, col, num):
        # 行
        if num in board[row]:
            return False
        # 列
        if num in (board[r][col] for r in range(self.SIZE)):
            return False
        # 宫
        br, bc = row // 3 * 3, col // 3 * 3
        for dr in range(3):
            for dc in range(3):
                if board[br + dr][bc + dc] == num:
                    return False
        return True

    # ── 绘制 ──

    def _draw(self):
        self._canvas.delete('all')
        for r in range(self.SIZE):
            for c in range(self.SIZE):
                x1 = c * self.CELL_SIZE + 1
                y1 = r * self.CELL_SIZE + 1
                x2 = x1 + self.CELL_SIZE - 2
                y2 = y1 + self.CELL_SIZE - 2

                # 背景
                if self._selected == (r, c):
                    fill = '#3a5a8a'  # 选中高亮
                elif (r, c) in self._conflicts:
                    fill = '#6b3030'  # 冲突红色
                elif self._given[r][c]:
                    fill = '#3a3a3a'  # 预置灰色
                else:
                    fill = '#2a2a2a'  # 默认

                self._canvas.create_rectangle(
                    x1, y1, x2, y2, fill=fill, outline='#444', width=1)

                # 数字
                val = self._board[r][c]
                if val != 0:
                    color = '#cccccc' if self._given[r][c] else '#4fc3f7'
                    self._canvas.create_text(
                        (x1 + x2) // 2, (y1 + y2) // 2,
                        text=str(val), fill=color,
                        font=self.FONT)

        # 粗边框 (3x3 宫)
        for i in range(4):
            x = i * 3 * self.CELL_SIZE
            self._canvas.create_line(x, 0, x, self.GRID_SIZE,
                                     fill='#888', width=2)
            y = i * 3 * self.CELL_SIZE
            self._canvas.create_line(0, y, self.GRID_SIZE, y,
                                     fill='#888', width=2)

    def _draw_win_overlay(self):
        """胜利时显示覆盖层"""
        self._canvas.create_rectangle(
            0, 0, self.GRID_SIZE, self.GRID_SIZE,
            fill='#1a3a1a', stipple='gray25', outline='')
        self._canvas.create_text(
            self.GRID_SIZE // 2, self.GRID_SIZE // 2,
            text='🎉 恭喜通关! 🎉',
            fill='#4caf50', font=('Segoe UI', 28, 'bold'))
