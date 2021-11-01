import sys
import os
import os.path as osp
import logging
from datetime import datetime

from qtpy.QtWidgets import QApplication  # 导入PyQt相关模块
from qtpy import QtCore

from eiseg import pjpath
from app import APP_EISeg  # 导入带槽的界面


def main():
    settings = QtCore.QSettings(
        osp.join(pjpath, "config/setting.ini"), QtCore.QSettings.IniFormat
    )

    logFolder = settings.value("logFolder")
    logLevel = settings.value("logLevel")
    logDays = settings.value("logDays")
    if logFolder is None or len(logFolder) == 0:
        logFolder = osp.join(pjpath, "log")
    if logLevel is None or len(logLevel) == 0:
        logLevel = eval("logging.DEBUG")
    if logDays is None or len(logDays) == 0:
        logDays = 7
    else:
        logDays = int(logDays)

    if not osp.exists(logFolder):
        os.makedirs(logFolder)

    # TODO: 删除大于logDays 的 log

    logging.basicConfig(
        level=logLevel,
        filename=osp.join(logFolder, f"eiseg-{datetime.now()}.log"),
        format="%(levelname)s - %(asctime)s - %(filename)s - %(funcName)s - %(message)s",
    )

    app = QApplication(sys.argv)
    lang = settings.value("language")
    if lang != "中文":
        trans = QtCore.QTranslator(app)
        trans.load(osp.join(pjpath, f"util/translate/{lang}"))
        app.installTranslator(trans)

    window = APP_EISeg()  # 创建对象
    window.currLanguage = lang
    window.showMaximized()  # 全屏显示窗口
    # 加载近期模型
    QApplication.processEvents()
    window.loadRecentModelParam()
    sys.exit(app.exec_())
