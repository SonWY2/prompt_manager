# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Prompt Manager GUI
Builds a single executable file with all dependencies bundled.
"""

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all PyQt6 submodules
pyqt6_hiddenimports = collect_submodules('PyQt6')

# Collect data files
datas = [
    ('src', 'src'),  # Include entire src directory
    ('public/logo.ico', 'public'),
    ('public/logo.svg', 'public'),
    ('src/config/prompt_improvement_templates.yaml', 'src/config'),
]

# Check if database exists and include it
if os.path.exists('src/backend/data'):
    datas.append(('src/backend/data', 'src/backend/data'))

# Check if settings file exists
if os.path.exists('src/gui/settings.json'):
    datas.append(('src/gui/settings.json', 'src/gui'))

a = Analysis(
    ['run_gui.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        'requests',
        'sqlite3',
        'json',
        'uuid',
        'datetime',
        'pathlib',
        'yaml',
        '_yaml',
        'difflib',
        're',
        'typing',
        'collections',
        'itertools',
        'functools',
        'operator',
        'copy',
    ] + pyqt6_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PromptManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Show console to see error messages
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='public/logo.ico' if os.path.exists('public/logo.ico') else None,
)
