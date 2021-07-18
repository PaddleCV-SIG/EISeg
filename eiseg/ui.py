from eiseg.widget.create import create_button, create_slider, create_text
import sys
import os.path as osp
from enum import Enum
from functools import partial

from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QGraphicsView

from eiseg import pjpath, __APPNAME__
import models
from util import MODELS, Instructions
from widget import LineItem, GripItem, AnnotationScene, AnnotationView
from widget.create import *
from major.remotesensing import createRSWorks


class Ui_EISeg(object):
    def setupUi(self, MainWindow):
        ## -- 主窗体设置 --
        MainWindow.setObjectName("MainWindow")
        MainWindow.setMinimumSize(QtCore.QSize(1366, 768))
        MainWindow.setWindowTitle(__APPNAME__)
        CentralWidget = QtWidgets.QWidget(MainWindow)
        CentralWidget.setObjectName("CentralWidget")
        MainWindow.setCentralWidget(CentralWidget)
        ## -----
        ## -- 工具栏 --
        toolBar = QtWidgets.QToolBar(self)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(toolBar.sizePolicy().hasHeightForWidth())
        toolBar.setSizePolicy(sizePolicy)
        toolBar.setMinimumSize(QtCore.QSize(0, 33))
        toolBar.setMovable(True)
        toolBar.setAllowedAreas(QtCore.Qt.BottomToolBarArea | QtCore.Qt.TopToolBarArea)
        toolBar.setObjectName("toolBar")
        self.toolBar = toolBar
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        ## -----
        ## -- 状态栏 --
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        self.statusbar.setStyleSheet("QStatusBar::item {border: none;}")
        MainWindow.setStatusBar(self.statusbar)
        self.statusbar.addPermanentWidget(
            self.show_logo(osp.join(pjpath, "resource/Paddle.png"))
        )
        ## -----
        ## -- 图形区域 --
        ImageRegion = QtWidgets.QHBoxLayout(CentralWidget)
        ImageRegion.setObjectName("ImageRegion")
        # 滑动区域
        self.scrollArea = QtWidgets.QScrollArea(CentralWidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        ImageRegion.addWidget(self.scrollArea)
        # 图形显示
        self.scene = AnnotationScene()

        QtWidgets.QShortcut(
            QtCore.Qt.Key_Escape,
            self,
            activated=partial(
                self.scene.setCreating,
                False,
            ),
        )

        self.scene.addPixmap(QtGui.QPixmap())
        self.canvas = AnnotationView(self.scene, self)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.canvas.setSizePolicy(sizePolicy)
        self.canvas.setAlignment(QtCore.Qt.AlignCenter)
        self.canvas.setAutoFillBackground(False)
        self.canvas.setStyleSheet("background-color: White")
        self.canvas.setObjectName("canvas")
        self.scrollArea.setWidget(self.canvas)
        ## -----
        ## -- 工作区 --
        self.dockWorker = QtWidgets.QDockWidget(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dockWorker.sizePolicy().hasHeightForWidth())
        self.dockWorker.setSizePolicy(sizePolicy)
        self.dockWorker.setMinimumSize(QtCore.QSize(71, 42))
        self.dockWorker.setWindowTitle(" ")  # 避免拖出后显示“python”
        self.dockWorker.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFloatable | 
            QtWidgets.QDockWidget.DockWidgetMovable
        )
        self.dockWorker.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea
        )
        self.dockWorker.setObjectName("dockWorker")
        p_create_button = partial(self.create_button, CentralWidget)
        # 设置区设置
        DockRegion = QtWidgets.QWidget()
        DockRegion.setObjectName("DockRegion")
        horizontalLayout = QtWidgets.QHBoxLayout(DockRegion)
        horizontalLayout.setObjectName("horizontalLayout")
        SetRegion = QtWidgets.QVBoxLayout()
        SetRegion.setObjectName("SetRegion")
        # 模型加载
        ModelRegion = QtWidgets.QVBoxLayout()
        ModelRegion.setObjectName("ModelRegion")
        labShowSet = self.create_text(CentralWidget, "labShowSet", "模型选择")
        ModelRegion.addWidget(labShowSet)
        combo = QtWidgets.QComboBox(self)
        combo.addItems([m.__name__ for m in MODELS])
        self.comboModelSelect = combo
        ModelRegion.addWidget(self.comboModelSelect)
        # 网络参数
        self.btnParamsSelect = p_create_button(
            "btnParamsLoad", "加载网络参数", osp.join(pjpath, "resource/Model.png"), "Ctrl+D"
        )
        ModelRegion.addWidget(self.btnParamsSelect)  # 模型选择
        SetRegion.addLayout(ModelRegion)
        SetRegion.setStretch(0, 1)
        # 数据列表
        # TODO: 数据列表加一个搜索功能
        listRegion = QtWidgets.QVBoxLayout()
        listRegion.setObjectName("listRegion")
        labFiles = self.create_text(CentralWidget, "labFiles", "数据列表")
        listRegion.addWidget(labFiles)
        self.listFiles = QtWidgets.QListWidget(CentralWidget)
        self.listFiles.setObjectName("listFiles")
        listRegion.addWidget(self.listFiles)
        # 标签列表
        labelListLab = self.create_text(CentralWidget, "labelListLab", "标签列表")
        listRegion.addWidget(labelListLab)
        # TODO: 改成 list widget
        self.labelListTable = QtWidgets.QTableWidget(CentralWidget)
        self.labelListTable.horizontalHeader().hide()
        # 铺满
        self.labelListTable.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )
        self.labelListTable.verticalHeader().hide()
        self.labelListTable.setColumnWidth(0, 10)
        # self.labelListTable.setMinimumWidth()
        self.labelListTable.setObjectName("labelListTable")
        listRegion.addWidget(self.labelListTable)
        self.btnAddClass = p_create_button(
            "btnAddClass", "添加标签", osp.join(pjpath, "resource/Label.png")
        )
        listRegion.addWidget(self.btnAddClass)
        SetRegion.addLayout(listRegion)
        SetRegion.setStretch(1, 20)
        # 滑块设置
        # 分割阈值
        p_create_slider = partial(self.create_slider, CentralWidget)
        ShowSetRegion = QtWidgets.QVBoxLayout()
        ShowSetRegion.setObjectName("ShowSetRegion")
        self.sldThresh, SegShowRegion = p_create_slider(
            "sldThresh", "labThresh", "分割阈值："
        )
        ShowSetRegion.addLayout(SegShowRegion)
        ShowSetRegion.addWidget(self.sldThresh)
        # 透明度
        self.sldOpacity, MaskShowRegion = p_create_slider(
            "sldOpacity", "labOpacity", "标签透明度："
        )
        ShowSetRegion.addLayout(MaskShowRegion)
        ShowSetRegion.addWidget(self.sldOpacity)
        # 点大小
        self.sldClickRadius, PointShowRegion = p_create_slider(
            "sldClickRadius", "labClickRadius", "点击可视化半径：", 3, 10, 1
        )
        ShowSetRegion.addLayout(PointShowRegion)
        ShowSetRegion.addWidget(self.sldClickRadius)
        SetRegion.addLayout(ShowSetRegion)
        SetRegion.setStretch(2, 1)
        # 保存
        self.btnSave = p_create_button(
            "btnSave", "保存", osp.join(pjpath, "resource/Save.png"), "Ctrl+S"
        )
        SetRegion.addWidget(self.btnSave)
        SetRegion.setStretch(3, 1)
        # dock设置完成
        horizontalLayout.addLayout(SetRegion)
        self.dockWorker.setWidget(DockRegion)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.dockWorker)
        ## 专业功能区工作区
        self.rsworker = createRSWorks(self, MainWindow, CentralWidget)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(1), self.rsworker)
        self.rsworker.hide()
        # TODO：添加医疗功能的工作区
        # self.miworker = createMIWorks(MainWindow, CentralWidget)
        # MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(1), self.miworker)
        # self.miworker.hide()
        ## -----
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    ## 创建文本
    def create_text(self, parent, text_name=None, text_text=None):
        return create_text(parent, text_name, text_text)

    ## 创建按钮
    def create_button(self, parent, btn_name, btn_text, ico_path=None, curt=None):
        return create_button(parent, btn_name, btn_text, ico_path, curt)

    ## 显示Logo
    def show_logo(self, logo_path):
        labLogo = QtWidgets.QLabel()
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum
        )
        labLogo.setSizePolicy(sizePolicy)
        labLogo.setMaximumSize(QtCore.QSize(100, 33))
        labLogo.setPixmap(QtGui.QPixmap(logo_path))
        labLogo.setScaledContents(True)
        labLogo.setObjectName("labLogo")
        return labLogo

    ## 创建滑块区域
    def create_slider(
        self,
        parent,
        sld_name,
        text_name,
        text,
        default_value=50,
        max_value=100,
        text_rate=0.01,
    ):
        return create_slider(
            parent,
            sld_name,
            text_name,
            text,
            default_value,
            max_value,
            text_rate,
        )

    def closeEvent(self, event):
        # 关闭主窗体退出程序，子窗体也关闭
        sys.exit(0)
