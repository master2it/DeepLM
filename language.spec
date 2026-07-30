# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for translator.exe
#
# Security: do NOT add `.env` (or any file containing HF_TOKEN) to `datas`.
# The packaged app reads HF_TOKEN from the Windows environment only.
# Configure with:  setx HF_TOKEN "hf_..."
# Then restart the terminal/app and run:  dist\translator.exe

a = Analysis(
    ['language.py'],
    pathex=[],
    binaries=[],
    datas=[],  # intentionally empty — never bundle .env
    hiddenimports=['config'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='translator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
