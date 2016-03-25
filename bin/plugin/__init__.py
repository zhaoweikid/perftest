# coding: utf-8
import os, sys
import glob
import traceback

HOME = os.path.dirname(os.path.abspath(__file__))
files = glob.glob(os.path.join(HOME, '[a-z]*.py'))
for f in files:
    try:
        __import__('plugin.'+os.path.basename(f)[:-3])
    except:
        traceback.print_exc()
        


