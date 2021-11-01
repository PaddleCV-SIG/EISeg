import sys
import os
import os.path as osp

import cv2

pjpath = osp.dirname(osp.realpath(__file__))

# TODO: 找相对import更好的方式
sys.path.insert(1, pjpath)
print(f"sys.path: {sys.path}")

__VERSION__ = "0.3.0.4"
__APPNAME__ = f"EISeg {__VERSION__}"

print(f"EISeg version: {__VERSION__}")

for k, v in os.environ.items():
    if k.startswith("QT_") and "cv2" in v:
        del os.environ[k]
