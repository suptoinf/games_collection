# 🎮 游戏合集 Game Collection

一个轻量级 Windows 桌面小游戏集合，支持**置顶显示**、**鼠标离开完全透明**等特性。

```
扫雷 💣  +  数独 🧩  更多游戏陆续添加中...
```

## ✨ 特性

- **Always-on-top** — 窗口始终在其他窗口之上，适合边看视频边玩
- **鼠标离开透明** — 可开关的透明模式，鼠标移出窗口后完全透明且点击穿透，不遮挡任何内容
- **可扩展架构** — 新增游戏只需创建一个 `tk.Frame` 子类，一行代码注册即可
- **单 exe 分发** — 可用 PyInstaller 打包成独立 exe，无需安装 Python

## 🎯 游戏

### 💣 扫雷 Minesweeper

| 项目 | 说明 |
|------|------|
| 棋盘 | 经典 9×9 |
| 雷数 | 10 |
| 操作 | 左键揭开 · 右键标旗 🚩 |
| 安全 | 首次点击不会踩雷（点完才布雷） |

### 🧩 数独 Sudoku

| 项目 | 说明 |
|------|------|
| 难度 | 简单 / 中等 / 困难 三档可调 |
| 输入 | 键盘数字键 或 底部数字按钮 |
| 提示 | 💡 按钮自动填入正确答案 |
| 检错 | 冲突格子自动高亮红色 |

## 🚀 快速开始

### 方式一：直接运行（需 Python）

```bash
pip install -r requirements.txt   # 可选（tkinter 为 Python 内置）
python main.py
```

> Python 自带 `tkinter`，无需额外安装。

### 方式二：打包成 exe

在 Windows 上：

```cmd
cd games_collection
.\build.bat
```

成功后 `dist\GameCollection.exe` 即为单文件可执行程序。

## 🖱️ 窗口操作

| 功能 | 说明 |
|------|------|
| 切换游戏 | 顶部工具栏 💣 扫雷 / 🧩 数独 |
| 透明模式 | 工具栏右侧 `👁 透明开/关` 按钮，默认关闭 |
| 鼠标离开 | 透明开启时，鼠标移出窗口 → 完全透明 + 点击穿透 |
| 鼠标回来 | 移回窗口 → 自动恢复不透明 |
| 窗口拖动 | 默认 Windows 标题栏拖动 |

## 🧩 新增游戏

1. 在目录下创建 `xxx.py`，定义一个继承 `tk.Frame` 的类：

```python
# xxx.py
import tkinter as tk

class YourGame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg='#1a1a1a')
        # 构建你的游戏 UI ...
```

2. 在 `main.py` 中注册：

```python
from xxx import YourGame
self._game_classes = {
    'minesweeper': Minesweeper,
    'sudoku': Sudoku,
    'xxx': YourGame,          # ← 加在这里
}
```

3. 工具栏按钮自动出现，无需其他修改。

## 📁 项目结构

```
games_collection/
├── main.py           # 主入口 — 窗口管理、透明控制、游戏切换
├── minesweeper.py    # 扫雷
├── sudoku.py         # 数独
├── build.bat         # Windows 一键打包脚本
├── build.spec        # PyInstaller 配置文件
└── .gitignore
```

## 📜 技术栈

- **Python 3.10+** — `tkinter` 标准库图形界面
- **Windows API** — `ctypes` 调用 `WS_EX_TRANSPARENT` 实现点击穿透
- **PyInstaller** — 打包为独立 exe
