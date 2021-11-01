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

    log_folder = osp.join(pjpath, "log")
    if not osp.exists(log_folder):
        os.makedirs(log_folder)
    # TODO: 删除一周以上的log
    logging.basicConfig(
        level=logging.DEBUG,
        filename=osp.join(log_folder, f"eiseg-{datetime.now()}.log"),
        format="%(levelname)s - %(asctime)s - %(message)s",
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
