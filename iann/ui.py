from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt


__APPNAME__ = "IANN"


class GraphicsView(QtWidgets.QGraphicsView):
    mouseClickdict = {Qt.LeftButton: "left", Qt.RightButton: "right", Qt.MidButton: "middle"}  # 分离出中键
    clickRequest = QtCore.pyqtSignal(int, int, str)  # 第三个int用于捕获鼠标按键

    def __init__(self, parent=None):
        super(GraphicsView, self).__init__(parent)
        self.point = QtCore.QPoint(0, 0)
        self.left_click = False
        self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setRenderHint(QtGui.QPainter.TextAntialiasing)

    def wheelEvent(self, event):
        # factor = 1.41 ** (-event.delta() / 240.0) 
        factor = event.angleDelta().y() / 120.0
        if event.angleDelta().y() / 120.0 > 0:
            factor=2
        else:
            factor=0.5
        self.scale(factor, factor)
        # 这里我觉得要限制一下大小

    def mousePressEvent(self, ev):
        print("view pos", ev.pos().x(), ev.pos().y())
        print("scene pos", self.mapToScene(ev.pos()))
        pos = self.mapToScene(ev.pos())
        if ev.buttons() in [Qt.LeftButton, Qt.RightButton]:
            self.clickRequest.emit(pos.x(), pos.y(), self.mouseClickdict[ev.buttons()])
        elif ev.buttons() == Qt.MidButton:
            self.left_click = True
            self._startPos = ev.pos()


class GraphicsPixmapItem(QtWidgets.QGraphicsPixmapItem):
    def __init__(self, pixmap):
        super(GraphicsPixmapItem, self).__init__(pixmap)


class UI_IANN(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        # MainWindow.resize(800, 600)
        MainWindow.setMinimumSize(QtCore.QSize(1366, 768))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("self.centralwidget")
        ImageRegion = QtWidgets.QHBoxLayout(self.centralwidget)
        ImageRegion.setObjectName("ImageRegion")
        self.scrollArea = QtWidgets.QScrollArea(self.centralwidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        ImageRegion.addWidget(self.scrollArea)
        ## -- 图形界面 --
        self.prevPoint = QtCore.QPoint()
        self.view = GraphicsView()
        self.scene = QtWidgets.QGraphicsScene(self)
        # self.scene.setSceneRect(0, 0, 512, 512)
        self.view.setScene(self.scene)
        self.scrollArea.setWidget(self.view)
        ## ----
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.dockWorker = QtWidgets.QDockWidget(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dockWorker.sizePolicy().hasHeightForWidth())
        self.dockWorker.setSizePolicy(sizePolicy)
        self.dockWorker.setMinimumSize(QtCore.QSize(71, 42))
        self.dockWorker.setWindowTitle("工作区")
        self.dockWorker.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable|QtWidgets.QDockWidget.DockWidgetMovable)
        self.dockWorker.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea|QtCore.Qt.RightDockWidgetArea)
        self.dockWorker.setObjectName("dockWorker")
        ## -- 工作区 --
        # 设置区设置
        self.DockRegion = QtWidgets.QWidget()
        self.DockRegion.setObjectName("DockRegion")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.DockRegion)
        self.horizontalLayout.setObjectName("horizontalLayout")
        SetRegion = QtWidgets.QVBoxLayout()
        SetRegion.setObjectName("SetRegion")
        ModelRegion = QtWidgets.QVBoxLayout()
        ModelRegion.setObjectName("ModelRegion")
        # 模型加载与选择
        labShowSet = QtWidgets.QLabel(self.centralwidget)
        labShowSet.setObjectName("labShowSet")
        labShowSet.setText("模型设置")
        ModelRegion.addWidget(labShowSet)
        self.btnModelSelect = self.create_button(
            self.centralwidget, "btnModelSelect", btn_text="模型选择", type="set"
        )
        self.button_add_menu(self.btnModelSelect, ["人像分割", "面部分割", "通用分割", "自定义模型"])
        ModelRegion.addWidget(self.btnModelSelect)  # 模型选择
        SetRegion.addLayout(ModelRegion)
        # 模型信息显示
        ModelInfoRegion = QtWidgets.QHBoxLayout()
        ModelInfoRegion.setObjectName("ModelInfoRegion")
        labModelNameInfo = QtWidgets.QLabel(self.centralwidget)
        labModelNameInfo.setObjectName("labModelNameInfo")
        labModelNameInfo.setText("当前模型：")
        ModelInfoRegion.addWidget(labModelNameInfo)
        self.labModelName = QtWidgets.QLabel(self.centralwidget)
        self.labModelName.setObjectName("labModelName")
        self.labModelName.setText("人像分割")
        ModelInfoRegion.addWidget(self.labModelName)
        # 划分比例
        ModelInfoRegion.setStretch(0, 1)
        ModelInfoRegion.setStretch(1, 10)
        SetRegion.addLayout(ModelInfoRegion)
        # 数据列表
        listRegion = QtWidgets.QVBoxLayout()
        listRegion.setObjectName("listRegion")
        labFiles = QtWidgets.QLabel(self.centralwidget)
        labFiles.setObjectName("labFiles")
        labFiles.setText("数据列表")
        listRegion.addWidget(labFiles)
        self.listFiles = QtWidgets.QListWidget(self.centralwidget)
        self.listFiles.setObjectName("listFiles")
        listRegion.addWidget(self.listFiles)
        labelListLab = QtWidgets.QLabel(self.centralwidget)
        labelListLab.setObjectName("labelListLab")
        labelListLab.setText("标签类别")
        listRegion.addWidget(labelListLab)
        self.labelListTable = QtWidgets.QTableWidget(self.centralwidget)
        self.labelListTable.setObjectName("labelListTable")
        listRegion.addWidget(self.labelListTable)
        self.btnAddClass = self.create_button(
            self.centralwidget, "btnAddClass", btn_text="添加标签", type="set"
        )
        listRegion.addWidget(self.btnAddClass)
        # 滑块设置
        SetRegion.addLayout(listRegion)
        ShowSetRegion = QtWidgets.QVBoxLayout()
        ShowSetRegion.setObjectName("ShowSetRegion")
        SegShowRegion = QtWidgets.QHBoxLayout()
        SegShowRegion.setObjectName("SegShowRegion")
        labSeg = QtWidgets.QLabel(self.centralwidget)
        labSeg.setObjectName("labSeg")
        labSeg.setText("分割阈值：")
        SegShowRegion.addWidget(labSeg)
        self.labThresh = QtWidgets.QLabel(self.centralwidget)
        self.labThresh.setObjectName("labThresh")
        self.labThresh.setText("0.5")
        SegShowRegion.addWidget(self.labThresh)
        SegShowRegion.setStretch(0, 1)
        SegShowRegion.setStretch(1, 10)
        ShowSetRegion.addLayout(SegShowRegion)
        self.sldThresh = QtWidgets.QSlider(self.centralwidget)
        self.sldThresh.setMaximum(10)  # 好像只能整数的，这里是扩大了10倍，1 -> 10
        self.sldThresh.setProperty("value", 5)
        self.sldThresh.setOrientation(QtCore.Qt.Horizontal)
        self.sldThresh.setObjectName("sldThresh")
        ShowSetRegion.addWidget(self.sldThresh)
        MaskShowRegion = QtWidgets.QHBoxLayout()
        MaskShowRegion.setObjectName("MaskShowRegion")
        labMask = QtWidgets.QLabel(self.centralwidget)
        labMask.setObjectName("labMask")
        labMask.setText("标签透明度：")
        MaskShowRegion.addWidget(labMask)
        self.labOpacity = QtWidgets.QLabel(self.centralwidget)
        self.labOpacity.setObjectName("labOpacity")
        self.labOpacity.setText("0.5")
        MaskShowRegion.addWidget(self.labOpacity)
        MaskShowRegion.setStretch(0, 1)
        MaskShowRegion.setStretch(1, 10)
        ShowSetRegion.addLayout(MaskShowRegion)
        self.sldOpacity = QtWidgets.QSlider(self.centralwidget)
        self.sldOpacity.setMaximum(10)
        self.sldOpacity.setSingleStep(1)
        self.sldOpacity.setProperty("value", 5)
        self.sldOpacity.setOrientation(QtCore.Qt.Horizontal)
        self.sldOpacity.setObjectName("sldOpacity")
        ShowSetRegion.addWidget(self.sldOpacity)
        PointShowRegion = QtWidgets.QHBoxLayout()
        PointShowRegion.setObjectName("PointShowRegion")
        labPointSzie = QtWidgets.QLabel(self.centralwidget)
        labPointSzie.setObjectName("labPointSzie")
        labPointSzie.setText("点击可视化半径：")
        PointShowRegion.addWidget(labPointSzie)
        self.labClickRadius = QtWidgets.QLabel(self.centralwidget)
        self.labClickRadius.setObjectName("labClickRadius")
        self.labClickRadius.setText("3")
        PointShowRegion.addWidget(self.labClickRadius)
        ShowSetRegion.addLayout(PointShowRegion)
        self.sldClickRadius = QtWidgets.QSlider(self.centralwidget)
        self.sldClickRadius.setMaximum(10)
        self.sldClickRadius.setMinimum(1)
        self.sldClickRadius.setSingleStep(1)
        self.sldClickRadius.setProperty("value", 3)
        self.sldClickRadius.setOrientation(QtCore.Qt.Horizontal)
        self.sldClickRadius.setObjectName("sldClickRadius")
        ShowSetRegion.addWidget(self.sldClickRadius)
        SetRegion.addLayout(ShowSetRegion)
        # 保存
        self.btnSave = self.create_button(
            self.centralwidget, "btnSave", btn_text="保存", type="set", curt="Ctrl+S"
        )
        SetRegion.addWidget(self.btnSave)
        SetRegion.setStretch(2, 10)
        # dock设置完成
        self.horizontalLayout.addLayout(SetRegion)
        self.dockWorker.setWidget(self.DockRegion)
        ## ----
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.dockWorker)
        self.toolBar = QtWidgets.QToolBar(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.toolBar.sizePolicy().hasHeightForWidth())
        self.toolBar.setSizePolicy(sizePolicy)
        self.toolBar.setMinimumSize(QtCore.QSize(0, 33))
        self.toolBar.setMovable(True)
        self.toolBar.setAllowedAreas(QtCore.Qt.BottomToolBarArea|QtCore.Qt.TopToolBarArea)
        self.toolBar.setObjectName("toolBar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.menuBar = QtWidgets.QMenuBar(MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 800, 26))
        self.menuBar.setObjectName("menuBar")
        self.menuFile = QtWidgets.QMenu(self.menuBar)
        self.menuFile.setObjectName("menuFile")
        self.menuSetting = QtWidgets.QMenu(self.menuBar)
        self.menuSetting.setObjectName("menuSetting")
        self.menuAbout = QtWidgets.QMenu(self.menuBar)
        self.menuAbout.setObjectName("menuAbout")
        self.menuHelp = QtWidgets.QMenu(self.menuBar)
        self.menuHelp.setObjectName("menuHelp")
        MainWindow.setMenuBar(self.menuBar)
        self.actLoadImage = QtWidgets.QAction(MainWindow)
        self.actLoadImage.setObjectName("actLoadImage")
        self.actOpenFolder = QtWidgets.QAction(MainWindow)
        self.actOpenFolder.setObjectName("actOpenFolder")
        self.actUndo = QtWidgets.QAction(MainWindow)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("iann/resources/undu.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actUndo.setIcon(icon)
        self.actUndo.setObjectName("actUndo")
        self.actRedo = QtWidgets.QAction(MainWindow)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("iann/resources/redu.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actRedo.setIcon(icon1)
        self.actRedo.setObjectName("actRedo")
        self.actClear = QtWidgets.QAction(MainWindow)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("iann/resources/clear.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actClear.setIcon(icon2)
        self.actClear.setObjectName("actClear")
        self.actFinish = QtWidgets.QAction(MainWindow)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("iann/resources/finish.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actFinish.setIcon(icon3)
        self.actFinish.setObjectName("actFinish")
        self.actPrevImg = QtWidgets.QAction(MainWindow)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap("iann/resources/left.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actPrevImg.setIcon(icon4)
        self.actPrevImg.setObjectName("actPrevImg")
        self.actNextImg = QtWidgets.QAction(MainWindow)
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap("iann/resources/right.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actNextImg.setIcon(icon5)
        self.actNextImg.setObjectName("actFinish")
        self.actScale = QtWidgets.QAction(MainWindow)
        self.actScale.setObjectName("actScale")
        self.actSave = QtWidgets.QAction(MainWindow)
        self.actSave.setObjectName("actSave")
        self.toolBar.addAction(self.actFinish)
        self.toolBar.addAction(self.actClear)
        self.toolBar.addAction(self.actUndo)
        self.toolBar.addAction(self.actRedo)
        self.toolBar.addAction(self.actPrevImg)
        self.toolBar.addAction(self.actNextImg)
        self.menuFile.addAction(self.actLoadImage)
        self.menuFile.addAction(self.actOpenFolder)
        self.menuSetting.addAction(self.actSave)
        self.menuSetting.addAction(self.actScale)
        self.menuBar.addAction(self.menuFile.menuAction())
        self.menuBar.addAction(self.menuSetting.menuAction())
        self.menuBar.addAction(self.menuHelp.menuAction())
        self.menuBar.addAction(self.menuAbout.menuAction())
        ## -- 进度条 --
        self.statusbar.setStyleSheet('QStatusBar::item {border: none;}')
        self.statusLabel = QtWidgets.QLabel()
        self.statusLabel.setText("当前进度：")
        self.progressBar = QtWidgets.QProgressBar()
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        labLogo = QtWidgets.QLabel()
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum
        )
        labLogo.setSizePolicy(sizePolicy)
        labLogo.setMaximumSize(QtCore.QSize(100, 33))
        labLogo.setPixmap(QtGui.QPixmap("iann/resources/paddle.png"))
        labLogo.setScaledContents(True)
        labLogo.setObjectName("labLogo")
        # 往状态栏中添加组件
        self.statusbar.addWidget(self.statusLabel)
        self.statusbar.addWidget(self.progressBar)
        self.statusbar.addPermanentWidget(labLogo)
        ## ----
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", __APPNAME__))
        self.toolBar.setWindowTitle(_translate("MainWindow", "toolBar"))
        self.menuFile.setTitle(_translate("MainWindow", "文件"))
        self.menuSetting.setTitle(_translate("MainWindow", "设置"))
        self.menuAbout.setTitle(_translate("MainWindow", "关于软件"))
        self.menuHelp.setTitle(_translate("MainWindow", "快速上手"))
        self.actLoadImage.setText(_translate("MainWindow", "加载图像"))
        self.actLoadImage.setShortcut(_translate("MainWindow", "Ctrl+A"))
        self.actOpenFolder.setText(_translate("MainWindow", "打开文件夹"))
        self.actOpenFolder.setShortcut(_translate("MainWindow", "Shift+A"))
        self.actUndo.setText(_translate("MainWindow", "撤销"))
        self.actUndo.setShortcut(_translate("MainWindow", "Ctrl+Z"))
        self.actRedo.setText(_translate("MainWindow", "重做"))
        self.actRedo.setShortcut(_translate("MainWindow", "Ctrl+Y"))
        self.actPrevImg.setText(_translate("MainWindow", "上一张"))
        self.actPrevImg.setShortcut(_translate("MainWindow", "A"))
        self.actNextImg.setText(_translate("MainWindow", "下一张"))
        self.actNextImg.setShortcut(_translate("MainWindow", "D"))
        self.actClear.setText(_translate("MainWindow", "清除"))
        self.actClear.setToolTip(_translate("MainWindow", "清除"))
        self.actClear.setShortcut(_translate("MainWindow", "Ctrl+Shift+Z"))
        self.actFinish.setText(_translate("MainWindow", "完成当前"))
        self.actFinish.setShortcut(_translate("MainWindow", "Space"))
        self.actScale.setText(_translate("MainWindow", "细粒度标注"))
        self.actSave.setText(_translate("MainWindow", "保存路径"))

    ## 创建按钮
    def create_button(
        self, parent, btn_name, btn_text=None, btn_ico=None, type="menu", curt=None
    ):
        # 创建和设置按钮
        if type == "menu":
            sizePolicy = QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
            )
            min_size = QtCore.QSize(0, 33)
            ico_size = QtCore.QSize(20, 20)
        elif type == "img":
            sizePolicy = QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum
            )
            min_size = QtCore.QSize(1, 0)
            ico_size = QtCore.QSize(30, 30)
        else:
            sizePolicy = QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed
            )
            min_size = QtCore.QSize(0, 40)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        btn = QtWidgets.QPushButton(parent)
        sizePolicy.setHeightForWidth(btn.sizePolicy().hasHeightForWidth())
        btn.setSizePolicy(sizePolicy)
        btn.setMinimumSize(min_size)
        btn.setObjectName(btn_name)
        # 设置名字
        btn.setText(btn_text if btn_text is not None else "")
        # 设置图标
        if btn_ico is not None:
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(btn_ico), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            btn.setIcon(icon)
            btn.setIconSize(ico_size)
        # 设置快捷键
        if curt is not None:
            btn.setShortcut(curt)
        return btn

    ## 按钮菜单
    def button_add_menu(self, button, name_list):
        menu = QtWidgets.QMenu()
        acts = []
        for name in name_list:
            act = QtWidgets.QAction(name, parent=menu)
            menu.addAction(act)
        button.setMenu(menu)
        button.Menu = menu