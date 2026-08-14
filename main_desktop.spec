# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from kivy_deps import sdl2, glew, angle

a = Analysis(
    ['main_desktop.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'kivy.core.window',
        'kivy.core.clipboard',
        'kivy.uix.boxlayout',
        'kivy.uix.textinput',
        'kivy.uix.button',
        'kivy.uix.label',
        'kivy.uix.spinner',
        'kivy.uix.progressbar',
        'kivy.uix.scrollview',
        'kivy.uix.image',
        'kivy.clock',
        'kivy.utils',
        'kivy.lang',
        'kivy.properties',
        'kivy.animation',
        'yt_dlp',
        'tkinter',
        'tkinter.filedialog',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'PIL', 'OpenGL', 'sqlite3', '_pytest', 'pytest', 'pygame', 'cv2', 'scipy', 'sklearn'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LasticProductions',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins + angle.dep_bins)],
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LasticProductions',
)
