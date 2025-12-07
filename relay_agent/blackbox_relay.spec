# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for BlackBox Relay Agent

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.py', '.'),
        ('*.yaml', '.'),
        ('*.json', '.'),
    ],
    hiddenimports=[
        'irsdk',
        'websockets',
        'websocket',
        'numpy',
        'cv2',
        'PIL',
        'psutil',
        'dotenv',
        'yaml',
        'pyaudio',
        'openai',
        'requests',
        'asyncio',
        'threading',
        'queue',
        'json',
        'logging',
        'dataclasses',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
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
    name='blackbox_relay',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to False for no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../desktop/assets/icon.ico',
)
