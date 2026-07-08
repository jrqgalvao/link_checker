# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\link_checker\\ui\\app.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('src\\link_checker\\ui\\templates\\link_checker_ui.html', 'link_checker\\ui\\templates'),
        ('assets\\logo_placeholder_white.svg', 'assets'),
        ('assets\\logo_placeholder_color.svg', 'assets'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'cryptography',
        'httpx',
        'lxml',
        'numpy',
        'numpy.libs',
        'pandas',
        'PIL',
        'pydantic',
        'pydantic_core',
        'pydantic_settings',
        'pyarrow',
        'playwright',
        'pytest',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name='LinkChecker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='assets\\app_icon.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    exclude_binaries=True,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LinkChecker',
)
