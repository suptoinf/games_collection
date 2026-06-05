"""
打飞机 (Shooter)
"""

import tkinter as tk
import random
import math
from typing import Optional


class Shooter(tk.Frame):
    """打飞机游戏"""

    W = 380
    H = 400
    TICK_MS = 30      # 毫秒/帧（约 33 fps）
    PLAYER_W = 36
    PLAYER_H = 30
    BULLET_W = 4
    BULLET_H = 12
    ENEMY_W = 30
    ENEMY_H = 26
    SPAWN_INTERVAL = 45  # 帧数间隔

    def __init__(self, parent, back_callback=None, scale=1.0):
        super().__init__(parent, bg='#1a1a1a')
        self._back_callback = back_callback
        self._scale = scale

        # 游戏状态
        self._player_x = 0.0
        self._bullets: list[dict] = []
        self._enemies: list[dict] = []
        self._score = 0
        self._high_score = 0
        self._running = False
        self._paused = False
        self._countdown = 0
        self._frame = 0
        self._tick_id: Optional[str] = None
        self._keys_down: set[str] = set()  # 当前按下的键

        self._setup_ui()
        self._new_game()

    # ── UI ──

    def _setup_ui(self):
        header = tk.Frame(self, bg='#1a1a1a')
        header.pack(fill=tk.X, padx=10, pady=(8, 4))

        if self._back_callback:
            back_btn = tk.Button(header, text='← 返回',
                                 font=('Segoe UI', 10),
                                 bg='#3a3a3a', fg='#aaa', relief=tk.FLAT,
                                 cursor='hand2', activebackground='#4a4a4a',
                                 command=self._back_callback)
            back_btn.pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(header, text='✈ 打飞机',
                 fg='#e0e0e0', bg='#1a1a1a',
                 font=('Segoe UI', 14, 'bold')).pack(side=tk.LEFT)

        self._score_label = tk.Label(header, text='0',
                                     fg='#ffd740', bg='#1a1a1a',
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
        cw = int(self.W * self._scale)
        ch = int(self.H * self._scale)
        self._canvas = tk.Canvas(self, width=cw, height=ch,
                                 bg='#0a0a1a', highlightthickness=0)
        self._canvas.pack(pady=(4, 10))
        self._canvas.focus_set()

        # 键盘
        self._canvas.bind('<KeyPress>', self._on_key_down)
        self._canvas.bind('<KeyRelease>', self._on_key_up)

    # ── 游戏逻辑 ──

    def _new_game(self):
        """开始新对局"""
        if self._tick_id:
            self.after_cancel(self._tick_id)
            self._tick_id = None

        self._player_x = self.W / 2
        self._bullets.clear()
        self._enemies.clear()
        self._score = 0
        self._frame = 0
        self._running = True
        self._paused = False
        self._countdown = 0
        self._score_label.config(text='0')
        self._draw()
        self._tick()

    def _spawn_enemy(self):
        """在顶部生成一个敌人"""
        w = random.randint(22, 36)
        h = random.randint(20, 30)
        x = random.uniform(w / 2, self.W - w / 2)
        speed = random.uniform(1.0, 2.8)
        hp = 1
        # 偶尔生成大敌人（需要两枪）
        if random.random() < 0.15:
            w = 40
            h = 34
            speed = 1.2
            hp = 2
        color = random.choice(['#ff5252', '#ff8a80', '#ea80fc', '#ff6e40'])
        self._enemies.append({
            'x': x, 'y': -h / 2, 'w': w, 'h': h,
            'speed': speed, 'color': color, 'hp': hp,
        })

    def _tick(self):
        """游戏循环帧"""
        if not self._running or self._paused:
            self._tick_id = self.after(self.TICK_MS, self._tick)
            return

        self._frame += 1
        speed = 4.0  # 玩家移动速度

        # 玩家移动
        if 'Left' in self._keys_down or 'a' in self._keys_down:
            self._player_x -= speed
        if 'Right' in self._keys_down or 'd' in self._keys_down:
            self._player_x += speed
        # 边界
        hw = self.PLAYER_W / 2
        self._player_x = max(hw, min(self.W - hw, self._player_x))

        # 自动射击（每 8 帧一发）
        if self._frame % 8 == 0:
            self._bullets.append({
                'x': self._player_x,
                'y': self.H - self.PLAYER_H / 2 - 6,
            })

        # 子弹移动
        for b in self._bullets:
            b['y'] -= 8
        self._bullets = [b for b in self._bullets if b['y'] > -20]

        # 生成敌人
        if self._frame % max(15, int(self.SPAWN_INTERVAL - self._frame * 0.003)) == 0:
            self._spawn_enemy()

        # 敌人移动（速度随帧数逐渐增加）
        speed_bonus = 1.0 + self._frame * 0.002
        for e in self._enemies:
            e['y'] += e['speed'] * speed_bonus

        # 碰撞检测：子弹 vs 敌人
        hit_any = False
        for b in self._bullets[:]:
            bx, by = b['x'], b['y']
            for e in self._enemies[:]:
                if abs(bx - e['x']) < e['w'] / 2 + 2 and abs(by - e['y']) < e['h'] / 2 + 2:
                    # 击中
                    e['hp'] -= 1
                    if b in self._bullets:
                        self._bullets.remove(b)
                    if e['hp'] <= 0:
                        self._enemies.remove(e)
                        self._score += 10 if e['w'] < 38 else 25
                        self._score_label.config(text=str(self._score))
                        hit_any = True
                    break

        # 碰撞检测：玩家 vs 敌人
        px, py = self._player_x, self.H - self.PLAYER_H / 2
        for e in self._enemies[:]:
            # 超出底部 → 移除
            if e['y'] - e['h'] / 2 > self.H:
                self._enemies.remove(e)
                continue
            # 撞到玩家
            if (abs(px - e['x']) < (self.PLAYER_W / 2 + e['w'] / 2 - 4) and
                    abs(py - e['y']) < (self.PLAYER_H / 2 + e['h'] / 2 - 4)):
                self._game_over('被击落了！')
                return

        # 清除逃出屏幕的敌人
        self._enemies = [e for e in self._enemies if e['y'] - e['h'] / 2 < self.H + 20]

        self._draw()
        self._tick_id = self.after(self.TICK_MS, self._tick)

    def _game_over(self, reason: str):
        """游戏结束"""
        self._running = False
        self._paused = False
        self._countdown = 0
        if self._tick_id:
            self.after_cancel(self._tick_id)
            self._tick_id = None

        if self._score > self._high_score:
            self._high_score = self._score

        self._draw()
        cw = int(self.W * self._scale)
        ch = int(self.H * self._scale)
        self._canvas.create_rectangle(0, 0, cw, ch,
                                       fill='#1a0000', stipple='gray25',
                                       outline='')
        self._canvas.create_text(cw // 2, ch // 2 - 12,
                                  text='💥 游戏结束',
                                  fill='#ff5252',
                                  font=('Segoe UI', 24, 'bold'))
        self._canvas.create_text(cw // 2, ch // 2 + 20,
                                  text=f'{reason}  得分: {self._score}',
                                  fill='#e0e0e0',
                                  font=('Segoe UI', 12))

    # ── 暂停/倒计时 ──

    def _do_countdown_step(self):
        self._countdown -= 1
        if self._countdown <= 0:
            self._paused = False
            self._draw()
        else:
            self._draw_countdown()
            self.after(1000, self._do_countdown_step)

    def _draw_pause(self):
        self._draw()
        cw = int(self.W * self._scale)
        ch = int(self.H * self._scale)
        self._canvas.create_rectangle(0, 0, cw, ch,
                                       fill='#0a0a1a', stipple='gray25',
                                       outline='')
        self._canvas.create_text(cw // 2, ch // 2 - 16,
                                  text='⏸ 暂停', fill='#ffd740',
                                  font=('Segoe UI', 22, 'bold'))
        self._canvas.create_text(cw // 2, ch // 2 + 14,
                                  text='按 空格键 继续', fill='#aaa',
                                  font=('Segoe UI', 11))

    def _draw_countdown(self):
        self._draw()
        cw = int(self.W * self._scale)
        ch = int(self.H * self._scale)
        self._canvas.create_rectangle(0, 0, cw, ch,
                                       fill='#0a1a0a', stipple='gray25',
                                       outline='')
        self._canvas.create_text(cw // 2, ch // 2 - 10,
                                  text=str(self._countdown),
                                  fill='#69f0ae',
                                  font=('Segoe UI', 48, 'bold'))
        self._canvas.create_text(cw // 2, ch // 2 + 30,
                                  text='准备...', fill='#aaa',
                                  font=('Segoe UI', 11))

    # ── 事件 ──

    def _on_key_down(self, event):
        self._keys_down.add(event.keysym)
        if event.keysym == 'space':
            if not self._running:
                self._new_game()
            elif self._paused:
                # 暂停中按空格 → 倒计时恢复
                self._countdown = 3
                self._draw_countdown()
                self._do_countdown_step()
            else:
                # 运行中按空格 → 暂停
                self._paused = True
                self._draw_pause()

    def _on_key_up(self, event):
        self._keys_down.discard(event.keysym)

    # ── 绘制 ──

    def _draw(self):
        self._canvas.delete('all')
        s = self._scale  # 缩放

        # 星空背景
        random.seed(42)
        for _ in range(40):
            sx = random.uniform(0, self.W)
            sy = random.uniform(0, self.H)
            sr = random.uniform(0.5, 1.5)
            self._canvas.create_oval(
                sx * s - sr, sy * s - sr, sx * s + sr, sy * s + sr,
                fill='#333', outline='')

        # 子弹
        for b in self._bullets:
            x1 = (b['x'] - self.BULLET_W / 2) * s
            y1 = (b['y'] - self.BULLET_H / 2) * s
            x2 = (b['x'] + self.BULLET_W / 2) * s
            y2 = (b['y'] + self.BULLET_H / 2) * s
            self._canvas.create_rectangle(
                x1, y1, x2, y2, fill='#ffd740', outline='')

        # 敌人
        for e in self._enemies:
            x1 = (e['x'] - e['w'] / 2) * s
            y1 = (e['y'] - e['h'] / 2) * s
            x2 = (e['x'] + e['w'] / 2) * s
            y2 = (e['y'] + e['h'] / 2) * s
            # 机身
            self._canvas.create_rectangle(
                x1, y1, x2, y2, fill=e['color'], outline='#fff', width=1)
            # 机翼
            self._canvas.create_polygon(
                (e['x'] - e['w'] / 2 * 0.3) * s, (e['y'] + e['h'] / 2) * s,
                (e['x'] + e['w'] / 2 * 0.3) * s, (e['y'] + e['h'] / 2) * s,
                (e['x']) * s, (e['y'] + e['h'] / 2 + 8) * s,
                fill=e['color'], outline='')
            # 血量指示（大敌人两枪）
            if e['hp'] > 1:
                self._canvas.create_text(
                    e['x'] * s, (e['y'] - e['h'] / 2 - 6) * s,
                    text='🛡', font=('Segoe UI', int(8 * s)))

        # 玩家飞机
        px, py = self._player_x, self.H - self.PLAYER_H / 2
        hw = self.PLAYER_W / 2
        hh = self.PLAYER_H / 2
        # 机身（三角形）
        self._canvas.create_polygon(
            px * s, (py - hh) * s,                    # 机头
            (px - hw) * s, (py + hh) * s,              # 左翼
            (px - hw * 0.4) * s, (py + hh * 0.6) * s,  # 左缩进
            (px + hw * 0.4) * s, (py + hh * 0.6) * s,  # 右缩进
            (px + hw) * s, (py + hh) * s,               # 右翼
            fill='#4fc3f7', outline='#e0e0e0', width=1)
        # 驾驶舱
        self._canvas.create_oval(
            (px - 4) * s, (py - hh * 0.4) * s,
            (px + 4) * s, (py + hh * 0.2) * s,
            fill='#b3e5fc', outline='')

        # 最高分
        if self._high_score > 0:
            self._canvas.create_text(
                6 * s, 6 * s, anchor='nw',
                text=f'🏆 最高: {self._high_score}',
                fill='#555', font=('Segoe UI', int(9 * s)))
