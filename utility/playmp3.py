# -*- coding: utf-8 -*-
"""
Created on Wed Jan 30 13:27:27 2019

@author: daniel
"""

import os

from pygame import mixer # Load the required library

workPath  = os.getcwd()
filePath  = "%s\\..\\tests\\sample_tmjl\\tmjl-turnon-light.mp3"%workPath

print(workPath)
print(filePath)

mixer.init()
mixer.music.load(filePath)
mixer.music.play()