import sys
import os.path as osp

pjpath = osp.dirname(osp.realpath(__file__))
sys.path.append(pjpath)

# 放在前面可以避免循环引用
# run中from了app的import
# app中import了eiseg的__APPNAME__
# 所以要使用下面两个from，应该将__APPNAME__放到前面
__APPNAME__ = "EISeg"


# from run import main
# from models import models