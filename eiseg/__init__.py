import sys
import os
import os.path as osp
import logging
from datetime import datetime

from qtpy import QtCore
import cv2

__APPNAME__ = "EISeg"
__VERSION__ = "0.4.0"


pjpath = osp.dirname(osp.realpath(__file__))
sys.path.append(pjpath)

for k, v in os.environ.items():
    if k.startswith("QT_") and "cv2" in v:
        del os.environ[k]

settings = QtCore.QSettings(
    osp.join(pjpath, "config/setting.ini"), QtCore.QSettings.IniFormat
)

logFolder = settings.value("logFolder")
logLevel = settings.value("logLevel")
logDays = settings.value("logDays")

if logFolder is None or len(logFolder) == 0:
    logFolder = osp.normcase(osp.join(pjpath, "log"))
if not osp.exists(logFolder):
    os.makedirs(logFolder)

if logLevel:
    logLevel = eval(logLevel)
else:
    logLevel = logging.DEBUG
if logDays:
    logDays = int(logDays)
else:
    logDays = 7
# TODO: 删除大于logDays 的 log

t = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
# logging.basicConfig(
#     level=logging.DEBUG,
#     filename=osp.normcase(osp.join(logFolder, f"eiseg-{t}.log")),
#     format="%(levelname)s - %(asctime)s - %(filename)s - %(funcName)s - %(message)s",
# )
logger = logging.getLogger("EISeg Logger")
handler = logging.FileHandler(osp.normcase(osp.join(logFolder, f"eiseg-{t}.log")))

handler.setFormatter(
    logging.Formatter(
        "%(levelname)s - %(asctime)s - %(filename)s - %(funcName)s - %(message)s"
    )
)
logger.addHandler(handler)
logger.info("test info")
