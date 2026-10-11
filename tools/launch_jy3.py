#!/usr/bin/env python3
"""jy3 啟動器：開 Ruffle 跑包內素材。PyInstaller --windowed 編成 金庸群俠傳3.exe。"""
import os
import sys
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from amf import pkg_root  # noqa: E402

pkg = pkg_root()
subprocess.Popen([
    os.path.join(pkg, 'resource', 'engine', 'ruffle.exe'),
    os.path.join(pkg, 'resource', 'assets', 'jy3', 'play.swf'),
    '--save-directory', os.path.join(pkg, 'save'),
])
