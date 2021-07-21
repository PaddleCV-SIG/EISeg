import sys

from qtpy.QtWidgets import QApplication  # 导入PyQt相关模块
from qtpy import QtCore
from eiseg import pjpath
import os.path as osp


def main():
    application = QApplication(sys.argv)
    trans = QtCore.QTranslator(application)
    trans.load(osp.join(pjpath, "util/translate/en_US"))
    print(trans.filePath(), trans.language())
    # print("app", QtCore.QCoreApplication.translate("APP_EISeg", "&编辑快捷键"))
    print(trans.isEmpty())
    application.installTranslator(trans)

    from app import APP_EISeg  # 导入带槽的界面

    myWin = APP_EISeg()  # 创建对象
    myWin.showMaximized()  # 全屏显示窗口
    # 加载近期模型
    QApplication.processEvents()
    myWin.loadRecentModelParam()
    sys.exit(application.exec_())
