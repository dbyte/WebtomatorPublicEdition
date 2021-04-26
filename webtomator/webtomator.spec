# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import shutil

import PyInstaller.config

# -------------------------------------------------------------------------------------
# NOTE: This file was modified by us. It's no more equal to the generated one by pyinstaller.
# NOTE: This file is intended to be started from terminal.
# -------------------------------------------------------------------------------------

# To create a standalone build for macos:
# 1. Open terminal and ACTIVATE the required python virtual environment!
# 2. If not installed, install pyinstaller via pip. Do so with command: pip install pyinstaller
# 3. cd to source folder 'webtomator' (lowercase!)
# 4. Run the following code in terminal to build a standalone version:
#           pyinstaller webtomator.spec
# 5. a) If there is an error saying something like ...dylib... not found, you have to download
#       a different Python version with enabled frameworks (macos) or enabled sharing (Windows).
#       On macos, do so with (example) command:
#           PYTHON_CONFIGURE_OPTS="--enable-framework" pyenv install 3.8.2
#       On Windows (example):
#           PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.7.7
#    b) After that, create a new virtualenv for that Python version with all your
#       project dependencies AND also pyinstaller in it.
#    c) Start again from 1.
# 6. On success, pyinstaller has created 2 directories within the Webtomator/webtomator/ directory.
#    The first is 'dist', second 'build'. In the dist folder, search for the
#    'Webtomator' binary and double-click to start the app. We don't know yet what the
#    build folder is for, seems it's not needed for execution.


# We create a custom location for pyinstaller's output.
customDistPath = Path("../dist")
customAppPath = customDistPath / "app"
customWorkPath = customDistPath / "build"
customAppPath.mkdir(parents=True, exist_ok=True)
customWorkPath.mkdir(parents=False, exist_ok=True)
PyInstaller.config.CONF['distpath'] = str(customAppPath)
PyInstaller.config.CONF['workpath'] = str(customWorkPath)
PyInstaller.config.CONF['specpath'] = str(customWorkPath)

block_cipher = None

a = Analysis(['webtomator.py'],
             pathex=['.'],
             binaries=[],
             datas=[('../userdata', 'userdata')],
             hiddenimports=['pkg_resources.py2_warn'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='Webtomator',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='Webtomator')

# Below are default directories created by pyinstaller. As we defined new directories
# for output above, they remain empty. Seems there is a glitch in pyinstaller which
# takes some hard coding of the default paths into account. Let's remove them.
shutil.rmtree(Path("dist"))  # dir possibly not empty, so use shutil instead of rmdir.
shutil.rmtree(Path("build"))  # dir possibly not empty, so use shutil instead of rmdir.