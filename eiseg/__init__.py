import sys
import os
import os.path as osp
import cv2

__APPNAME__ = "EISeg"
__VERSION__ = "0.4.0"


pjpath = osp.dirname(osp.realpath(__file__))
sys.path.append(pjpath)

for k, v in os.environ.items():
    if k.startswith("QT_") and "cv2" in v:
        del os.environ[k]