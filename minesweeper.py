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


# 难度配置
_DIFFICULTIES = {
    '简单':  {'rows': 9,  'cols': 9,  'mines': 10, 'label': '简单'},
    '中等':  {'rows': 16, 'cols': 16, 'mines': 40, 'label': '中等'},
    '困难':  {'rows': 16, 'cols': 30, 'mines': 99, 'label': '困难'},
}
_DIFF_NAMES = ['简单', '中等', '困难']


class Minesweeper(tk.Frame):
    """扫雷游戏"""

    CELL_SIZE = 42  # 基准格子大小

    def __init__(self, parent, back_callback=None, scale=1.0):
        super().__init__(parent, bg='#1a1a1a')
        self._back_callback = back_callback
        self._scale = scale
        self._board: list[list[int]] = []
        self._revealed: list[list[bool]] = []
        self._flagged: list[list[bool]] = []
        self._game_over = False
        self._first_click = True
        self._flag_count = 0
        self._mines_placed = False
        self._difficulty = '简单'

        self._setup_ui()
        self._set_difficulty('简单')
        # 窗口映射后尺寸才准确，延迟重算
        self.after(400, lambda: self._set_difficulty(self._difficulty))

    # ── UI 构建 ──

    def _setup_ui(self):
        # 顶栏：返回 + 难度 + 雷计数 + 状态表情 + 重置按钮
        header = tk.Frame(self, bg='#1a1a1a')
        header.pack(fill=tk.X, padx=10, pady=(8, 4))

        if self._back_callback:
            back_btn = tk.Button(header, text='← 返回',
                                 font=('Segoe UI', 10),
                                 bg='#3a3a3a', fg='#aaa', relief=tk.FLAT,
                                 cursor='hand2', activebackground='#4a4a4a',
                                 command=self._back_callback)
            back_btn.pack(side=tk.LEFT, padx=(0, 8))

        # 难度按钮
        btn_s = {'bg': '#3a3a3a', 'fg': 'white', 'relief': tk.FLAT,
                 'font': ('Segoe UI', 9), 'padx': 6, 'pady': 1,
                 'cursor': 'hand2', 'activebackground': '#4a4a4a'}
        self._diff_btns: dict[str, tk.Button] = {}
        for diff in _DIFF_NAMES:
            btn = tk.Button(header, text=diff, **btn_s,
                            command=lambda d=diff: self._set_difficulty(d))
            btn.pack(side=tk.LEFT, padx=1)
            self._diff_btns[diff] = btn

        self._mine_label = tk.Label(header, text='💣 10',
                                    fg='#e0e0e0', bg='#1a1a1a',
                                    font=('Segoe UI', 14, 'bold'))
        self._mine_label.pack(side=tk.LEFT, padx=(6, 0))

        self._face_label = tk.Label(header, text='🙂',
                                    fg='#e0e0e0', bg='#1a1a1a',
                                    font=('Segoe UI', 22))
        self._face_label.pack(side=tk.LEFT, expand=True)

        reset_btn = tk.Button(header, text='🔄', font=('Segoe UI', 14),
                              bg='#3a3a3a', fg='white', relief=tk.FLAT,
                              cursor='hand2', activebackground='#4a4a4a',
                              command=self._reset)
        reset_btn.pack(side=tk.RIGHT)

        # 画布（尺寸由 _set_difficulty 动态设置）
        self._canvas = tk.Canvas(self, width=100, height=100,
                                 bg='#2a2a2a', highlightthickness=0)
        self._canvas.pack(pady=(4, 10))

        self._canvas.bind('<Button-1>', self._on_left_click)
        self._canvas.bind('<Button-2>', self._on_right_click)  # macOS
        self._canvas.bind('<Button-3>', self._on_right_click)  # Windows

    # ── 难度切换 ──

    def _set_difficulty(self, diff: str):
        """切换难度（重新创建画布并开始新对局）"""
        self._difficulty = diff
        cfg = _DIFFICULTIES[diff]
        self.rows = cfg['rows']
        self.cols = cfg['cols']
        self.mines = cfg['mines']

        # 根据窗口实际可用空间计算格子大小
        self.update_idletasks()
        scale = self._scale
        avail_w = max(200, self.winfo_width() - 20)
        avail_h = max(200, self.winfo_height() - 80)
        logical_w = avail_w / scale
        logical_h = avail_h / scale
        cell_w = int(logical_w / self.cols)
        cell_h = int(logical_h / self.rows)
        self.cell_size = max(14, min(cell_w, cell_h))

        # 更新画布尺寸
        cw = self.cols * self.cell_size
        ch = self.rows * self.cell_size
        self._canvas.config(width=cw, height=ch)

        # 高亮当前难度
        for name, btn in self._diff_btns.items():
            btn.config(bg='#5a7a5a' if name == diff else '#3a3a3a')

        self._reset()

    # ── 游戏逻辑 ──

    def _reset(self):
        """重置游戏"""
        self._board = [[0] * self.cols for _ in range(self.rows)]
        self._revealed = [[False] * self.cols for _ in range(self.rows)]
        self._flagged = [[False] * self.cols for _ in range(self.rows)]
        self._game_over = False
        self._first_click = True
        self._mines_placed = False
        self._flag_count = 0
        self._mine_label.config(text=f'💣 {self.mines}')
        self._face_label.config(text='🙂')
        self._draw()

    def _place_mines(self, safe_r: int, safe_c: int):
        """布雷（避开首次点击位置及其 3×3 邻域）"""
        safe = {(safe_r + dr, safe_c + dc)
                for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                if 0 <= safe_r + dr < self.rows and 0 <= safe_c + dc < self.cols}

        positions = [(r, c) for r in range(self.rows) for c in range(self.cols)
                     if (r, c) not in safe]
        random.shuffle(positions)

        for i in range(min(self.mines, len(positions))):
            r, c = positions[i]
            self._board[r][c] = -1  # -1 = 雷

        # 计算数字
        for r in range(self.rows):
            for c in range(self.cols):
                if self._board[r][c] == -1:
                    continue
                cnt = 0
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.rows and 0 <= nc < self.cols and self._board[nr][nc] == -1:
                            cnt += 1
                self._board[r][c] = cnt

        self._mines_placed = True

    def _reveal(self, r: int, c: int):
        """递归翻开格子"""
        if not (0 <= r < self.rows and 0 <= c < self.cols):
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
        for r in range(self.rows):
            for c in range(self.cols):
                if self._board[r][c] == -1:
                    self._revealed[r][c] = True

    def _check_win(self):
        """检查是否胜利"""
        for r in range(self.rows):
            for c in range(self.cols):
                if self._board[r][c] != -1 and not self._revealed[r][c]:
                    return
        self._game_over = True
        self._face_label.config(text='🎉')

    # ── 事件处理 ──

    def _on_left_click(self, event):
        if self._game_over:
            return

        c = event.x // self.cell_size
        r = event.y // self.cell_size
        if not (0 <= r < self.rows and 0 <= c < self.cols):
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

        c = event.x // self.cell_size
        r = event.y // self.cell_size
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return
        if self._revealed[r][c]:
            return

        self._flagged[r][c] = not self._flagged[r][c]
        self._flag_count += 1 if self._flagged[r][c] else -1
        remaining = self.mines - self._flag_count
        self._mine_label.config(text=f'💣 {max(remaining, 0)}')
        self._draw()

    # ── 绘制 ──

    def _draw(self):
        self._canvas.delete('all')
        fs = max(8, min(14, self.cell_size // 2))  # 自适应字体
        for r in range(self.rows):
            for c in range(self.cols):
                x1 = c * self.cell_size + 1
                y1 = r * self.cell_size + 1
                x2 = x1 + self.cell_size - 2
                y2 = y1 + self.cell_size - 2

                if self._revealed[r][c]:
                    val = self._board[r][c]
                    if val == -1:
                        # 地雷
                        self._canvas.create_rectangle(
                            x1, y1, x2, y2, fill='#ff6b6b', outline='#555', width=1)
                        self._canvas.create_text(
                            (x1 + x2) // 2, (y1 + y2) // 2,
                            text='💣', font=('Segoe UI', fs))
                    else:
                        fill = '#d4d4d4'
                        self._canvas.create_rectangle(
                            x1, y1, x2, y2, fill=fill, outline='#999', width=1)
                        if val > 0:
                            self._canvas.create_text(
                                (x1 + x2) // 2, (y1 + y2) // 2,
                                text=str(val),
                                fill=_NUMBER_COLORS.get(val, 'black'),
                                font=('Segoe UI', fs, 'bold'))
                elif self._flagged[r][c]:
                    self._canvas.create_rectangle(
                        x1, y1, x2, y2, fill='#4a4a4a', outline='#444', width=1)
                    self._canvas.create_text(
                        (x1 + x2) // 2, (y1 + y2) // 2,
                        text='🚩', font=('Segoe UI', fs))
                else:
                    # 未翻开
                    self._canvas.create_rectangle(
                        x1, y1, x2, y2,
                        fill='#3a6ea5', outline='#4a7db5', width=1)
