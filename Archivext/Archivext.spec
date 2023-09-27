# -*- mode: python ; coding: utf-8 -*-

from src._meta import __appname__

added_files = [
    ('src/data/img/archivext.ico', 'data/img'),
    ('src/data/img/eye.png', 'data/img'),
    ('src/data/img/eye2.png', 'data/img'),
    ('src/data/img/loading.gif', 'data/img'),
    ('src/data/img/success.gif', 'data/img'),
    ('src/data/img/fail.gif', 'data/img'),
    ('src/data/img/copy.png', 'data/img'),
    ('src/data/img/copy2.png', 'data/img'),
    ('src/data/img/info.png', 'data/img')
]

a = Analysis(
    ['src\\Archivext.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'doctest', 'unittest', 'xml', 'xmlrpc', 'difflib', 'optparse',
        'ftplib', 'optparse', 'pdb', 'pydoc', 'pyexpat', 'pywintypes',
        'socketserver', 'win32api', 'win32con',
        'netbios', 'netrc', 'pkgutil', 'plistlib', 'pprint',
        'py_compile', 'runpy', 'win32wnet',
        '_osx_support', '_strptime', 'getopt',
        'getpass', 'operators',
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
    name=__appname__,
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
    icon=['src/data/img/archivext.ico'],
)
