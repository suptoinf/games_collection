"""
游戏合集主入口 - 扫雷 & 数独
Windows 11 支持：置顶、鼠标离开透明、点击穿透
"""

import tkinter as tk
import ctypes
from ctypes import wintypes

# Windows API 常量
WS_EX_TRANSPARENT = 0x20
WS_EX_LAYERED = 0x80000
GWL_EXSTYLE = -20

# Windows API 函数
user32 = ctypes.windll.user32


# 启用高 DPI 感知（解决 200% 缩放下屏幕尺寸不准确的问题）
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass  # 非 Windows 或旧版本系统忽略


def set_click_through(hwnd: int, enabled: bool):
    """启用/禁用窗口点击穿透（鼠标事件穿透到下层窗口）"""
    if not hwnd:
        return
    ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    if enabled:
        ex_style |= WS_EX_TRANSPARENT
    else:
        ex_style &= ~WS_EX_TRANSPARENT
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)


class GameCollection:
    """游戏合集主窗口"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎮 游戏合集")

        # ── 窗口置顶 ──
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 1.0)

        # 延迟初始化：HWND 获取 + 屏幕自适应定位
        self.hwnd = None
        self.root.after(100, self._init_hwnd)
        self.root.after(150, self._position_bottom_right)

        # ── 鼠标悬停透明（可配置，默认关闭）──
        self._transparent_alpha = 0.0      # 完全透明
        self._opaque_alpha = 1.0
        self._transparent_enabled = False   # 默认关闭
        self._is_transparent = False        # 当前透明状态

        # ── UI ──
        self._setup_ui()

        # ── 注册游戏 ──
        from minesweeper import Minesweeper
        from sudoku import Sudoku
        from snake import Snake
        # (emoji, 中文名, class)
        self._game_classes: dict[str, tuple[str, str, type]] = {
            'minesweeper': ('💣', '扫雷', Minesweeper),
            'sudoku': ('🧩', '数独', Sudoku),
            'snake': ('🐍', '贪吃蛇', Snake),
        }
        self._current_game: str | None = None

        # 启动鼠标位置轮询（代替 Enter/Leave 事件）
        self._start_polling()

        # 启动 → 显示主菜单
        self.root.after(200, self._show_menu)

    def _init_hwnd(self):
        """获取窗口句柄（Windows HWND）"""
        self.root.update_idletasks()
        try:
            # tkinter winfo_id() 返回的是 Canvas/Frame 句柄，需 GetParent 获取顶级窗口
            self.hwnd = user32.GetParent(self.root.winfo_id())
        except Exception:
            self.hwnd = None

    def _get_dpi_scale(self):
        """获取 DPI 缩放比例（100%=1.0, 200%=2.0）"""
        try:
            return self.root.winfo_fpixels('1i') / 96.0
        except Exception:
            return 1.0

    def _position_bottom_right(self):
        """将窗口定位在屏幕右下角（自适应 DPI 缩放）"""
        self.root.update_idletasks()
        scale = self._get_dpi_scale()
        base_w = 420
        base_h = 520
        win_w = int(base_w * scale)
        win_h = int(base_h * scale)
        pad = int(30 * scale)  # 距右下角边距
        try:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            x = max(0, sw - win_w - pad)
            y = max(0, sh - win_h - pad)
            self.root.geometry(f"{win_w}x{win_h}+{x}+{y}")
        except Exception:
            # 保底位置
            self.root.geometry(f"{win_w}x{win_h}+{pad}+{pad}")

    def _setup_ui(self):
        """构建主 UI（内容区 + 底部状态栏）"""
        # ── 内容区（菜单或游戏）──
        self._content = tk.Frame(self.root, bg='#1a1a1a')
        self._content.pack(fill=tk.BOTH, expand=True)

        # ── 底部状态栏（始终可见）──
        bottom = tk.Frame(self.root, bg='#2d2d2d', height=36)
        bottom.pack(fill=tk.X, side=tk.BOTTOM)
        bottom.pack_propagate(False)

        tk.Label(bottom, text='🎮 游戏合集',
                 fg='#777', bg='#2d2d2d',
                 font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=10)

        btn_s = {'bg': '#3a3a3a', 'fg': 'white', 'relief': tk.FLAT,
                 'font': ('Segoe UI', 10), 'padx': 10, 'pady': 2,
                 'cursor': 'hand2', 'activebackground': '#4a4a4a'}

        self._btn_transparent = tk.Button(
            bottom, text='👁 透明关', **btn_s,
            command=self._toggle_transparent)
        self._btn_transparent.pack(side=tk.RIGHT, padx=4, pady=4)

    # ── 页面导航 ──

    def _show_menu(self):
        """显示主菜单（游戏入口卡片）"""
        for w in self._content.winfo_children():
            w.destroy()
        self._current_game = None

        frame = tk.Frame(self._content, bg='#1a1a1a')
        frame.place(relx=0.5, rely=0.45, anchor=tk.CENTER)

        tk.Label(frame, text='🎮', fg='#e0e0e0', bg='#1a1a1a',
                 font=('Segoe UI', 40)).pack()
        tk.Label(frame, text='游戏合集', fg='#e0e0e0', bg='#1a1a1a',
                 font=('Segoe UI', 20, 'bold')).pack(pady=(2, 24))

        cards = tk.Frame(frame, bg='#1a1a1a')
        cards.pack()

        for name, (emoji, title, _) in self._game_classes.items():
            btn = tk.Button(
                cards,
                text=f'{emoji}\n{title}',
                font=('Segoe UI', 16),
                bg='#2a2a2a', fg='#e0e0e0',
                relief=tk.RAISED, bd=2,
                width=7, height=3,
                cursor='hand2',
                activebackground='#3d3d3d',
                command=lambda n=name: self._navigate_to_game(n))
            btn.pack(side=tk.LEFT, padx=8)

        tk.Label(frame, text='选择一个游戏开始',
                 fg='#555', bg='#1a1a1a',
                 font=('Segoe UI', 10)).pack(pady=(20, 0))

    def _navigate_to_game(self, name: str):
        """进入指定游戏"""
        for w in self._content.winfo_children():
            w.destroy()

        _, _, cls = self._game_classes[name]
        instance = cls(self._content, back_callback=self._show_menu)
        instance.pack(fill=tk.BOTH, expand=True)
        self._current_game = name

    # ── 鼠标透明控制 ──

    def _toggle_transparent(self):
        """开关透明模式"""
        self._transparent_enabled = not self._transparent_enabled
        if self._transparent_enabled:
            self._btn_transparent.config(text='👁 透明开', bg='#5a5a3a')
        else:
            # 关闭透明 → 立刻恢复
            self._btn_transparent.config(text='👁 透明关', bg='#3a3a3a')
            self._restore_opaque()

    def _restore_opaque(self):
        """恢复不透明 + 取消点击穿透"""
        self.root.attributes('-alpha', self._opaque_alpha)
        set_click_through(self.hwnd, False)
        self._is_transparent = False

    def _make_transparent(self):
        """变为完全透明 + 启用点击穿透"""
        self.root.attributes('-alpha', self._transparent_alpha)
        set_click_through(self.hwnd, True)
        self._is_transparent = True

    def _start_polling(self):
        """启动鼠标位置轮询（替代 Enter/Leave 事件，更可靠）"""
        self._poll_mouse()

    def _poll_mouse(self):
        """每隔 500ms 检查鼠标是否在窗口内"""
        if not self._transparent_enabled:
            # 透明关闭时确保窗口可见
            if self._is_transparent:
                self._restore_opaque()
            self.root.after(500, self._poll_mouse)
            return

        try:
            px = self.root.winfo_pointerx()
            py = self.root.winfo_pointery()
            wx = self.root.winfo_rootx()
            wy = self.root.winfo_rooty()
            ww = self.root.winfo_width()
            wh = self.root.winfo_height()
        except Exception:
            self.root.after(500, self._poll_mouse)
            return

        inside = (wx <= px <= wx + ww and wy <= py <= wy + wh)

        if inside and self._is_transparent:
            # 鼠标回到窗口 → 恢复
            self._restore_opaque()
        elif not inside and not self._is_transparent:
            # 鼠标离开窗口 → 透明
            self._make_transparent()

        self.root.after(500, self._poll_mouse)

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    app = GameCollection()
    app.run()
