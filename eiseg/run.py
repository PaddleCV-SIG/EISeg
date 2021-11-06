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
    ## -- log --
    settings = QtCore.QSettings(
        osp.join(pjpath, "config/setting.ini"), QtCore.QSettings.IniFormat
    )
    #
    # logFolder = settings.value("logFolder")
    # logLevel = settings.value("logLevel")
    # logDays = settings.value("logDays")
    #
    # if logFolder is None or len(logFolder) == 0:
    #     logFolder = osp.normcase(osp.join(pjpath, "log"))
    # if not osp.exists(logFolder):
    #     os.makedirs(logFolder)
    #
    # if logLevel:
    #     logLevel = eval(logLevel)
    # else:
    #     logLevel = logging.DEBUG
    # if logDays:
    #     logDays = int(logDays)
    # else:
    #     logDays = 7
    # # TODO: 删除大于logDays 的 log
    #
    # t = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # logging.basicConfig(
    #     level=logging.DEBUG,
    #     filename=osp.normcase(osp.join(logFolder, f"eiseg-{t}.log")),
    #     format="%(levelname)s - %(asctime)s - %(filename)s - %(funcName)s - %(message)s",
    # )
    # logger = logging.getLogger("EISeg Logger")
    # handler = logging.FileHandler(osp.normcase(osp.join(logFolder, f"eiseg-{t}.log")))
    #
    # handler.setFormatter(
    #     logging.Formatter(
    #         "%(levelname)s - %(asctime)s - %(filename)s - %(funcName)s - %(message)s"
    #     )
    # )
    # logger.addHandler(handler)
    # logger.info("test info")
    #
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
    sys.exit(app.exec())
