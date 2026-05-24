"""
扫雷 (Minesweeper) — 经典 9×9, 10 雷
"""

import tkinter as tk
import random
from typing import Optional

# 颜色映射 (数字 → 颜色)
_NUMBER_COLORS = {
    1: '#0000ff', 2: '#008000', 3: '#ff0000', 4: '#000080',
    5: '#800000', 6: '#008080', 7: '#000000', 8: '#808080',
}


class Minesweeper(tk.Frame):
    """扫雷游戏"""

    # ── 配置 ──
    ROWS = 9
    COLS = 9
    MINES = 10
    CELL_SIZE = 42

    def __init__(self, parent):
        super().__init__(parent, bg='#1a1a1a')
        self._board: list[list[int]] = []
        self._revealed: list[list[bool]] = []
        self._flagged: list[list[bool]] = []
        self._game_over = False
        self._first_click = True
        self._flag_count = 0
        self._mines_placed = False

        self._setup_ui()
        self._reset()

    # ── UI 构建 ──

    def _setup_ui(self):
        # 顶栏：雷计数 + 状态表情 + 重置按钮
        header = tk.Frame(self, bg='#1a1a1a')
        header.pack(fill=tk.X, padx=10, pady=(8, 4))

        self._mine_label = tk.Label(header, text='💣 10',
                                    fg='#e0e0e0', bg='#1a1a1a',
                                    font=('Segoe UI', 14, 'bold'))
        self._mine_label.pack(side=tk.LEFT)

        self._face_label = tk.Label(header, text='🙂',
                                    fg='#e0e0e0', bg='#1a1a1a',
                                    font=('Segoe UI', 22))
        self._face_label.pack(side=tk.LEFT, expand=True)

        reset_btn = tk.Button(header, text='🔄', font=('Segoe UI', 14),
                              bg='#3a3a3a', fg='white', relief=tk.FLAT,
                              cursor='hand2', activebackground='#4a4a4a',
                              command=self._reset)
        reset_btn.pack(side=tk.RIGHT)

        # 画布
        cw = self.COLS * self.CELL_SIZE
        ch = self.ROWS * self.CELL_SIZE
        self._canvas = tk.Canvas(self, width=cw, height=ch,
                                 bg='#2a2a2a', highlightthickness=0)
        self._canvas.pack(pady=(4, 10))

        self._canvas.bind('<Button-1>', self._on_left_click)
        self._canvas.bind('<Button-2>', self._on_right_click)  # macOS
        self._canvas.bind('<Button-3>', self._on_right_click)  # Windows

    # ── 游戏逻辑 ──

    def _reset(self):
        """重置游戏"""
        self._board = [[0] * self.COLS for _ in range(self.ROWS)]
        self._revealed = [[False] * self.COLS for _ in range(self.ROWS)]
        self._flagged = [[False] * self.COLS for _ in range(self.ROWS)]
        self._game_over = False
        self._first_click = True
        self._mines_placed = False
        self._flag_count = 0
        self._mine_label.config(text=f'💣 {self.MINES}')
        self._face_label.config(text='🙂')
        self._draw()

    def _place_mines(self, safe_r: int, safe_c: int):
        """布雷（避开首次点击位置及其 3×3 邻域）"""
        safe = {(safe_r + dr, safe_c + dc)
                for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                if 0 <= safe_r + dr < self.ROWS and 0 <= safe_c + dc < self.COLS}

        positions = [(r, c) for r in range(self.ROWS) for c in range(self.COLS)
                     if (r, c) not in safe]
        random.shuffle(positions)

        for i in range(min(self.MINES, len(positions))):
            r, c = positions[i]
            self._board[r][c] = -1  # -1 = 雷

        # 计算数字
        for r in range(self.ROWS):
            for c in range(self.COLS):
                if self._board[r][c] == -1:
                    continue
                cnt = 0
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.ROWS and 0 <= nc < self.COLS and self._board[nr][nc] == -1:
                            cnt += 1
                self._board[r][c] = cnt

        self._mines_placed = True

    def _reveal(self, r: int, c: int):
        """递归翻开格子"""
        if not (0 <= r < self.ROWS and 0 <= c < self.COLS):
            return
        if self._revealed[r][c] or self._flagged[r][c]:
            return

        self._revealed[r][c] = True

        # 踩雷
        if self._board[r][c] == -1:
            self._game_over = True
            self._face_label.config(text='💥')
            self._reveal_all_mines()
            self._draw()
            return

        # 空格 → 自动展开
        if self._board[r][c] == 0:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    self._reveal(r + dr, c + dc)

        self._draw()
        self._check_win()

    def _reveal_all_mines(self):
        """失败时翻开所有地雷"""
        for r in range(self.ROWS):
            for c in range(self.COLS):
                if self._board[r][c] == -1:
                    self._revealed[r][c] = True

    def _check_win(self):
        """检查是否胜利"""
        for r in range(self.ROWS):
            for c in range(self.COLS):
                if self._board[r][c] != -1 and not self._revealed[r][c]:
                    return
        self._game_over = True
        self._face_label.config(text='🎉')

    # ── 事件处理 ──

    def _on_left_click(self, event):
        if self._game_over:
            return

        c = event.x // self.CELL_SIZE
        r = event.y // self.CELL_SIZE
        if not (0 <= r < self.ROWS and 0 <= c < self.COLS):
            return
        if self._flagged[r][c]:
            return

        if self._first_click:
            self._first_click = False
            self._place_mines(r, c)

        self._reveal(r, c)

    def _on_right_click(self, event):
        if self._game_over:
            return

        c = event.x // self.CELL_SIZE
        r = event.y // self.CELL_SIZE
        if not (0 <= r < self.ROWS and 0 <= c < self.COLS):
            return
        if self._revealed[r][c]:
            return

        self._flagged[r][c] = not self._flagged[r][c]
        self._flag_count += 1 if self._flagged[r][c] else -1
        remaining = self.MINES - self._flag_count
        self._mine_label.config(text=f'💣 {max(remaining, 0)}')
        self._draw()

    # ── 绘制 ──

    def _draw(self):
        self._canvas.delete('all')
        for r in range(self.ROWS):
            for c in range(self.COLS):
                x1 = c * self.CELL_SIZE + 1
                y1 = r * self.CELL_SIZE + 1
                x2 = x1 + self.CELL_SIZE - 2
                y2 = y1 + self.CELL_SIZE - 2

                if self._revealed[r][c]:
                    val = self._board[r][c]
                    if val == -1:
                        # 地雷
                        self._canvas.create_rectangle(
                            x1, y1, x2, y2, fill='#ff6b6b', outline='#555', width=1)
                        self._canvas.create_text(
                            (x1 + x2) // 2, (y1 + y2) // 2,
                            text='💣', font=('Segoe UI', 16))
                    else:
                        fill = '#d4d4d4'
                        self._canvas.create_rectangle(
                            x1, y1, x2, y2, fill=fill, outline='#999', width=1)
                        if val > 0:
                            self._canvas.create_text(
                                (x1 + x2) // 2, (y1 + y2) // 2,
                                text=str(val),
                                fill=_NUMBER_COLORS.get(val, 'black'),
                                font=('Segoe UI', 14, 'bold'))
                elif self._flagged[r][c]:
                    self._canvas.create_rectangle(
                        x1, y1, x2, y2, fill='#4a4a4a', outline='#444', width=1)
                    self._canvas.create_text(
                        (x1 + x2) // 2, (y1 + y2) // 2,
                        text='🚩', font=('Segoe UI', 16))
                else:
                    # 未翻开
                    self._canvas.create_rectangle(
                        x1, y1, x2, y2,
                        fill='#3a6ea5', outline='#4a7db5', width=1)
