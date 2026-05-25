"""
贪吃蛇 (Snake)
"""

import tkinter as tk
import random
from typing import Optional

# 方向常量
_DIR = {
    'Up': (0, -1),
    'Down': (0, 1),
    'Left': (-1, 0),
    'Right': (1, 0),
}
_REVERSE = {'Up': 'Down', 'Down': 'Up', 'Left': 'Right', 'Right': 'Left'}


class Snake(tk.Frame):
    """贪吃蛇游戏"""

    COLS = 20
    ROWS = 16
    CELL_SIZE = 24
    TICK_MS = 180  # 毫秒/帧

    def __init__(self, parent):
        super().__init__(parent, bg='#1a1a1a')

        self._snake: list[tuple[int, int]] = []   # 蛇身 [(r,c), ...]
        self._food: Optional[tuple[int, int]] = None
        self._direction = 'Right'
        self._next_dir = 'Right'
        self._running = False
        self._score = 0
        self._high_score = 0
        self._tick_id: Optional[str] = None

        self._setup_ui()
        self._new_game()

    # ── UI ──

    def _setup_ui(self):
        header = tk.Frame(self, bg='#1a1a1a')
        header.pack(fill=tk.X, padx=10, pady=(8, 4))

        tk.Label(header, text='🐍 贪吃蛇',
                 fg='#e0e0e0', bg='#1a1a1a',
                 font=('Segoe UI', 14, 'bold')).pack(side=tk.LEFT)

        self._score_label = tk.Label(header, text='0',
                                     fg='#4fc3f7', bg='#1a1a1a',
                                     font=('Segoe UI', 14, 'bold'))
        self._score_label.pack(side=tk.RIGHT, padx=4)

        tk.Label(header, text='🏆',
                 fg='#e0e0e0', bg='#1a1a1a',
                 font=('Segoe UI', 12)).pack(side=tk.RIGHT, padx=(4, 0))

        btn_style = {'bg': '#3a3a3a', 'fg': 'white', 'relief': tk.FLAT,
                     'font': ('Segoe UI', 10), 'padx': 10, 'pady': 2,
                     'cursor': 'hand2', 'activebackground': '#4a4a4a'}

        self._restart_btn = tk.Button(header, text='🔄 重来', **btn_style,
                                      command=self._new_game)
        self._restart_btn.pack(side=tk.RIGHT, padx=4)

        # 画布
        cw = self.COLS * self.CELL_SIZE
        ch = self.ROWS * self.CELL_SIZE
        self._canvas = tk.Canvas(self, width=cw, height=ch,
                                 bg='#0f0f0f', highlightthickness=0)
        self._canvas.pack(pady=(4, 10))
        self._canvas.focus_set()

        # 键盘
        self._canvas.bind('<Key>', self._on_key)

    # ── 游戏逻辑 ──

    def _new_game(self):
        """开始新对局"""
        if self._tick_id:
            self.after_cancel(self._tick_id)
            self._tick_id = None

        mid_c = self.COLS // 2
        mid_r = self.ROWS // 2
        self._snake = [(mid_r, mid_c), (mid_r, mid_c - 1), (mid_r, mid_c - 2)]
        self._direction = 'Right'
        self._next_dir = 'Right'
        self._score = 0
        self._running = True
        self._score_label.config(text='0')
        self._spawn_food()
        self._draw()
        self._tick()

    def _spawn_food(self):
        """在空地生成食物"""
        occupied = set(self._snake)
        free = [(r, c) for r in range(self.ROWS) for c in range(self.COLS)
                if (r, c) not in occupied]
        if free:
            self._food = random.choice(free)
        else:
            self._food = None  # 蛇占满棋盘 → 胜利

    def _tick(self):
        """游戏循环帧"""
        if not self._running:
            return

        self._direction = self._next_dir
        dr, dc = _DIR[self._direction]
        head = self._snake[0]
        new_head = (head[0] + dr, head[1] + dc)

        # 碰墙
        if not (0 <= new_head[0] < self.ROWS and 0 <= new_head[1] < self.COLS):
            self._game_over('撞墙！')
            return

        # 吃食物
        ate = (new_head == self._food)

        # 碰自身（提前检查，移除尾部后再检查吃食物的情况）
        if ate:
            self._snake.insert(0, new_head)  # 先长
        else:
            self._snake.insert(0, new_head)
            tail = self._snake.pop()  # 再缩

        # 碰自身（新头不能与除尾部外的身体重叠；但因为尾部已弹出，只需检查头是否重复）
        if self._snake[0] in self._snake[1:]:
            self._game_over('咬到自己了！')
            return

        if ate:
            self._score += 1
            self._score_label.config(text=str(self._score))
            self._spawn_food()
            if self._food is None:
                self._game_over('🎉 满分通关！')
                return

        self._draw()
        self._tick_id = self.after(self.TICK_MS, self._tick)

    def _game_over(self, reason: str):
        """游戏结束"""
        self._running = False
        if self._tick_id:
            self.after_cancel(self._tick_id)
            self._tick_id = None

        if self._score > self._high_score:
            self._high_score = self._score

        # 显示结束画面
        self._draw()
        cw = self.COLS * self.CELL_SIZE
        ch = self.ROWS * self.CELL_SIZE
        self._canvas.create_rectangle(0, 0, cw, ch,
                                       fill='#1a0a0a', stipple='gray25',
                                       outline='')
        self._canvas.create_text(cw // 2, ch // 2 - 12,
                                  text='💀 游戏结束',
                                  fill='#ff5252',
                                  font=('Segoe UI', 24, 'bold'))
        self._canvas.create_text(cw // 2, ch // 2 + 20,
                                  text=f'{reason}  得分: {self._score}',
                                  fill='#e0e0e0',
                                  font=('Segoe UI', 12))

    # ── 事件 ──

    def _on_key(self, event):
        if event.keysym in _DIR:
            # 不允许 180 度掉头
            if event.keysym != _REVERSE.get(self._direction):
                self._next_dir = event.keysym
        elif event.keysym == 'space':
            if not self._running:
                self._new_game()

    # ── 绘制 ──

    def _draw(self):
        self._canvas.delete('all')

        # 网格线（淡灰）
        for x in range(0, self.COLS * self.CELL_SIZE + 1, self.CELL_SIZE):
            self._canvas.create_line(x, 0, x, self.ROWS * self.CELL_SIZE,
                                     fill='#1a1a1a', width=1)
        for y in range(0, self.ROWS * self.CELL_SIZE + 1, self.CELL_SIZE):
            self._canvas.create_line(0, y, self.COLS * self.CELL_SIZE, y,
                                     fill='#1a1a1a', width=1)

        # 食物
        if self._food:
            fx = self._food[1] * self.CELL_SIZE + self.CELL_SIZE // 2
            fy = self._food[0] * self.CELL_SIZE + self.CELL_SIZE // 2
            self._canvas.create_oval(
                fx - 7, fy - 7, fx + 7, fy + 7,
                fill='#ff5252', outline='')

        # 蛇身
        for i, (r, c) in enumerate(self._snake):
            x1 = c * self.CELL_SIZE + 2
            y1 = r * self.CELL_SIZE + 2
            x2 = x1 + self.CELL_SIZE - 4
            y2 = y1 + self.CELL_SIZE - 4
            # 头部渐变亮色
            color = '#69f0ae' if i == 0 else '#4caf50'
            self._canvas.create_rectangle(
                x1, y1, x2, y2, fill=color, outline='#2e7d32', width=1)

        # 蛇眼（头部）
        if self._snake:
            hr, hc = self._snake[0]
            cx = hc * self.CELL_SIZE + self.CELL_SIZE // 2
            cy = hr * self.CELL_SIZE + self.CELL_SIZE // 2
            dr, dc = _DIR[self._direction]
            # 两只眼睛
            for side in (-1, 1):
                ex = cx + dc * 5 + side * (-dc if dc else 3)
                ey = cy + dr * 5 + side * (-dr if dr else 2)
                self._canvas.create_oval(
                    ex - 2, ey - 2, ex + 2, ey + 2,
                    fill='white', outline='')

        # 最高分
        if self._high_score > 0:
            self._canvas.create_text(
                6, 6, anchor='nw',
                text=f'🏆 最高: {self._high_score}',
                fill='#666', font=('Segoe UI', 9))
