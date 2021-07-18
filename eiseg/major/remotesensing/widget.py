from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt

import os.path as osp
from functools import partial

from eiseg import pjpath, __APPNAME__
from widget.create import *


def createRSWorks(app, MainWindow, CentralWidget):
    ## -- 工作区 --
    rsDockWorker = QtWidgets.QDockWidget(MainWindow)
    sizePolicy = QtWidgets.QSizePolicy(
        QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
    )
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(rsDockWorker.sizePolicy().hasHeightForWidth())
    rsDockWorker.setSizePolicy(sizePolicy)
    rsDockWorker.setMinimumSize(QtCore.QSize(71, 42))
    rsDockWorker.setWindowTitle("遥感标注设置")
    rsDockWorker.setFeatures(
        QtWidgets.QDockWidget.DockWidgetFloatable | 
        QtWidgets.QDockWidget.DockWidgetMovable
    )
    rsDockWorker.setAllowedAreas(
        QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea
    )
    rsDockWorker.setObjectName("rsDockWorker")
    p_create_button = partial(create_button, CentralWidget)
    # 设置区设置
    DockRegion = QtWidgets.QWidget()
    DockRegion.setObjectName("DockRegion")
    horizontalLayout = QtWidgets.QHBoxLayout(DockRegion)
    horizontalLayout.setObjectName("horizontalLayout")
    SetRegion = QtWidgets.QVBoxLayout()
    SetRegion.setObjectName("SetRegion")
    # 格式选择
    FormatRegion = QtWidgets.QVBoxLayout()
    FormatRegion.setObjectName("FormatRegion")
    labShowSet = create_text(CentralWidget, "formatSelection", "格式选择")
    FormatRegion.addWidget(labShowSet)
    FormatCombo = QtWidgets.QComboBox()
    FormatCombo.addItems(["*.tif"])  # "*.img"
    FormatRegion.addWidget(FormatCombo)
    SetRegion.addLayout(FormatRegion)
    SetRegion.setStretch(0, 1)
    # 波段选择
    bandRegion = QtWidgets.QVBoxLayout()
    bandRegion.setObjectName("bandRegion")
    labFiles = create_text(CentralWidget, "bandSelection", "波段设置")
    bandRegion.addWidget(labFiles)
    text_list = ["R", "G", "B"]
    combos = []
    for txt in text_list:
        lab = create_text(CentralWidget, "band" + txt, txt)
        combo = QtWidgets.QComboBox()
        combo.addItems(["band_" + txt])
        combos.append(combo)
        hbandLayout = QtWidgets.QHBoxLayout()
        hbandLayout.setObjectName("hbandLayout")
        hbandLayout.addWidget(lab)
        hbandLayout.addWidget(combo)
        hbandLayout.setStretch(1, 4)
        bandRegion.addLayout(hbandLayout)
    SetRegion.addLayout(bandRegion)
    SetRegion.setStretch(1, 1)
    # 滑块设置
    # 分割阈值
    p_create_slider = partial(create_slider, CentralWidget)
    ShowSetRegion = QtWidgets.QVBoxLayout()
    ShowSetRegion.setObjectName("ShowSetRegion")
    sldBrightness, BrightnessRegion = p_create_slider(
        "sldBrightness", "labBrightness", "亮度："
    )
    ShowSetRegion.addLayout(BrightnessRegion)
    ShowSetRegion.addWidget(sldBrightness)
    # 透明度
    sldContrast, ContrastRegion = p_create_slider(
        "sldContrast", "labContrast", "对比度："
    )
    ShowSetRegion.addLayout(ContrastRegion)
    ShowSetRegion.addWidget(sldContrast)
    SetRegion.addLayout(ShowSetRegion)
    SetRegion.setStretch(2, 1)
    # 空间信息
    InfoRegion = QtWidgets.QVBoxLayout()
    InfoRegion.setObjectName("InfoRegion")
    Lab = create_text(CentralWidget, "spaceInfo", "空间信息")
    InfoRegion.addWidget(Lab)
    infoListTable = QtWidgets.QTableWidget(CentralWidget)
    infoListTable.horizontalHeader().hide()
    # 铺满
    infoListTable.horizontalHeader().setSectionResizeMode(
        QtWidgets.QHeaderView.Stretch
    )
    infoListTable.verticalHeader().hide()
    infoListTable.setColumnWidth(0, 10)
    # infoListTable.setMinimumWidth()
    infoListTable.setObjectName("infoListTable")
    InfoRegion.addWidget(infoListTable)
    SetRegion.addLayout(InfoRegion)
    SetRegion.setStretch(3, 40)
    # dock设置完成
    horizontalLayout.addLayout(SetRegion)
    rsDockWorker.setWidget(DockRegion)
    MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(2), rsDockWorker)
    # 赋值
    app.combo_rs_format = FormatCombo
    app.comboList_rs_rgb= combos
    app.sldBrightness = sldBrightness
    app.sldContrast = sldContrast
    app.ListTable_rs_space = infoListTable
    return rsDockWorker