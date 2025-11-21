# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for building the TranslatePPT Windows executable."""
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

project_root = Path(__file__).parent

datas = [
    (str(project_root / "frontend"), "frontend"),
    (str(project_root / ".env.example"), "."),
]

for package in ("langdetect", "pptx", "docx", "openpyxl"):
    datas.extend(collect_data_files(package))

block_cipher = None


a = Analysis(
    ['run_app.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TranslatePPT',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TranslatePPT',
)
