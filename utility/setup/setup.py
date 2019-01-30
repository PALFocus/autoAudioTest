# -*- coding: utf-8 -*-
"""
Created on Fri Jan 25 16:56:54 2019

@author: daniel
"""

# setup.py

from distutils.core import setup
import py2exe
import sys

#this allows to run it with a simple double click.
sys.argv.append('py2exe')

py2exe_options = {
        "compressed": 1,
        "optimize": 2,
        "ascii": 0,
        "bundle_files": 1,        # 其中bundle_files有效值为：
                                  # 3 (默认)不打包。
                                  # 2 打包，但不打包Python解释器。
                                  # 1 打包，包括Python解释器。
#        "dll_excludes": ["MSVCP90.dll",],
        }
setup(
      name = 'console demo',
      version = '1.0',
      console = ['autoAudioTest.py',],   # console 命令行执行程序
                                 # windows  窗口执行程序
      zipfile = None,
      options = {'py2exe': py2exe_options}
      )
