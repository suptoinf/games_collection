# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 构建配置
生成单个 exe，无控制台窗口，含 tkinter 支持
"""

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'tkinter',
        'minesweeper',
        'sudoku',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的库以减小体积
        'matplotlib', 'numpy', 'pandas', 'PIL', 'Pillow',
        'cv2', 'scipy', 'sympy', 'notebook', 'jupyter',
        'test', 'unittest', 'distutils',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='游戏合集',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # 无控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='icon.ico',     # 可选：放一个 icon.ico 在同目录，取消注释即可
)
