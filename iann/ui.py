from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt

__APPNAME__ = "IANN"


class Canvas(QtWidgets.QGraphicsView):
    clickRequest = QtCore.Signal(int, int, bool)

    def __init__(self, *args):
        super(Canvas, self).__init__(*args)

    def wheelEvent(self, event):
        print("in")
        if event.modifiers() & QtCore.Qt.ControlModifier:
            print(event.angleDelta().x(), event.angleDelta().y())
            # self.zoom += event.angleDelta().y() / 2880
            zoom = 1 + event.angleDelta().y() / 2880

            self.scale(zoom, zoom)
            event.ignore()
        else:
            super(Canvas, self).wheelEvent(event)

    def mousePressEvent(self, ev):
        print("view pos", ev.pos().x(), ev.pos().y())
        print("scene pos", self.mapToScene(ev.pos()))
        pos = self.mapToScene(ev.pos())
        self.clickRequest.emit(pos.x(), pos.y(), ev.buttons() == Qt.LeftButton)


class Ui_IANN(object):
    def setupUi(self, MainWindow):
        ## 窗体设置
        MainWindow.setObjectName("MainWindow")
        # MainWindow.resize(1366, 768)
        MainWindow.setMinimumSize(QtCore.QSize(1366, 768))
        MainWindow.setWindowTitle(__APPNAME__)
        ## 控件区域设置
        CentralWidget = QtWidgets.QWidget(MainWindow)
        CentralWidget.setObjectName("CentralWidget")
        MainLayout = QtWidgets.QVBoxLayout(CentralWidget)
        MainLayout.setObjectName("MainLayout")
        # 顶部按MenuRegion钮
        MenuRegion = QtWidgets.QHBoxLayout()
        MenuRegion.setObjectName("MenuRegion")
        self.btnOpenImage = self.create_button(
            CentralWidget, "btnOpenImage", btn_text="打开图片", curt="Ctrl+O"
        )
        MenuRegion.addWidget(self.btnOpenImage)
        self.btnOpenFolder = self.create_button(
            CentralWidget, "btnOpenFolder", btn_text="打开文件夹", curt="Ctrl+Shift+O"
        )
        MenuRegion.addWidget(self.btnOpenFolder)  # 打开文件夹
        self.btnUndo = self.create_button(
            CentralWidget,
            "btnUndo",
            btn_text="撤销",
            btn_ico="resources/undo.png",
            curt="Ctrl+Z",
        )
        MenuRegion.addWidget(self.btnUndo)  # 撤销
        self.btnRedo = self.create_button(
            CentralWidget,
            "btnRedo",
            btn_text="重做",
            btn_ico="resources/redo.png",
            curt="Ctrl+Y",
        )
        MenuRegion.addWidget(self.btnRedo)  # 重做
        self.btnUndoAll = self.create_button(
            CentralWidget, "btnUndoAll", btn_text="撤销全部", curt="Ctrl+Shift+Z"
        )
        # IDEA: 重做最后一个目标，感觉全部重做不是很实用
        MenuRegion.addWidget(self.btnUndoAll)  # 重做
        self.btnFinishObject = self.create_button(
            CentralWidget, "btnFinishObject", btn_text="完成当前目标"
        )
        MenuRegion.addWidget(self.btnFinishObject)  # 重做

        # IDEA: 重做最后一个目标，感觉全部重做不是很实用
        MenuRegion.addWidget(self.btnUndoAll)  # 重做

        self.btnScale = self.create_button(CentralWidget, "btnScale", btn_text="细粒度标注")
        self.button_add_menu(self.btnScale, ["四宫格", "九宫格"])
        MenuRegion.addWidget(self.btnScale)  # 细粒度标注
        self.btnAbout = self.create_button(CentralWidget, "btnAbout", btn_text="关于软件")
        MenuRegion.addWidget(self.btnAbout)  # 关于
        self.btnHelp = self.create_button(CentralWidget, "btnHelp", btn_text="快速上手")
        self.button_add_menu(self.btnHelp, ["文档", "操作流程"])
        MenuRegion.addWidget(self.btnHelp)  # 帮助
        # 分隔符号
        spacerItem = QtWidgets.QSpacerItem(
            20, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        MenuRegion.addItem(spacerItem)
        # paddle-logo
        labLogo = QtWidgets.QLabel(CentralWidget)
        labLogo.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum
        )
        labLogo.setSizePolicy(sizePolicy)
        labLogo.setMaximumSize(QtCore.QSize(100, 33))
        labLogo.setPixmap(QtGui.QPixmap("resources/paddle.png"))
        labLogo.setScaledContents(True)
        labLogo.setObjectName("labLogo")
        MenuRegion.addWidget(labLogo)
        # 菜单栏按钮比例
        MenuRegion.setStretch(0, 2)
        MenuRegion.setStretch(2, 1)
        MenuRegion.setStretch(3, 1)
        MenuRegion.setStretch(4, 2)
        MenuRegion.setStretch(5, 2)
        MenuRegion.setStretch(6, 2)
        MenuRegion.setStretch(7, 4)
        MainLayout.addLayout(MenuRegion)

        # 图像区域
        ImageRegion = QtWidgets.QHBoxLayout()
        ImageRegion.setObjectName("ImageRegion")
        self.btnPrevImg = self.create_button(
            CentralWidget,
            "btnPrevImg",
            btn_ico="resources/prevImg.png",
            type="img",
            curt="A",
        )
        ImageRegion.addWidget(self.btnPrevImg)  # 上一张图
        # 图片区域
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.addPixmap(QtGui.QPixmap())
        self.canvas = Canvas(self.scene, self)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.canvas.setSizePolicy(sizePolicy)
        self.canvas.setAlignment(QtCore.Qt.AlignCenter)
        self.canvas.setAutoFillBackground(False)
        self.canvas.setStyleSheet("background-color: White")
        self.canvas.setObjectName("canvas")
        ImageRegion.addWidget(self.canvas)
        self.btnNextImg = self.create_button(
            CentralWidget,
            "btnNextImg",
            btn_ico="resources/nextImg.png",
            type="img",
            curt="D",
        )
        ImageRegion.addWidget(self.btnNextImg)  # 下一张图
        # 图像区域比例
        ImageRegion.setStretch(0, 1)
        ImageRegion.setStretch(1, 18)
        ImageRegion.setStretch(2, 1)
        MainLayout.addLayout(ImageRegion)
        # 显示标注进度
        ProgressRegion = QtWidgets.QHBoxLayout()
        ProgressRegion.setObjectName("ProgressRegion")
        spacerItem1 = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        ProgressRegion.addItem(spacerItem1)
        labProgress = QtWidgets.QLabel(CentralWidget)
        labProgress.setObjectName("labProgress")
        labProgress.setText("当前进度：")
        ProgressRegion.addWidget(labProgress)
        self.progressBar = QtWidgets.QProgressBar(CentralWidget)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        ProgressRegion.addWidget(self.progressBar)
        spacerItem2 = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        ProgressRegion.addItem(spacerItem2)
        ProgressRegion.setStretch(0, 2)
        ProgressRegion.setStretch(1, 1)
        ProgressRegion.setStretch(2, 19)
        ProgressRegion.setStretch(3, 2)
        MainLayout.addLayout(ProgressRegion)
        ## 主窗口设置完毕
        MainLayout.setStretch(0, 1)
        MainLayout.setStretch(1, 18)
        MainLayout.setStretch(2, 1)
        MainWindow.setCentralWidget(CentralWidget)

        ## 右侧dock widget
        self.DockWidget = QtWidgets.QDockWidget(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        self.DockWidget.setSizePolicy(sizePolicy)
        self.DockWidget.setFloating(False)
        self.DockWidget.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea
        )
        self.DockWidget.setObjectName("DockWidget")
        self.DockWidget.setWindowTitle("工作区")
        self.DockWidget.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFloatable
            | QtWidgets.QDockWidget.DockWidgetMovable
        )
        self.DockRegion = QtWidgets.QWidget()
        self.DockRegion.setObjectName("DockRegion")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.DockRegion)
        self.horizontalLayout.setObjectName("horizontalLayout")
        # 设置区设置
        SetRegion = QtWidgets.QVBoxLayout()
        SetRegion.setObjectName("SetRegion")
        ModelRegion = QtWidgets.QVBoxLayout()
        ModelRegion.setObjectName("ModelRegion")
        # 模型加载与选择
        labShowSet = QtWidgets.QLabel(CentralWidget)
        labShowSet.setObjectName("labShowSet")
        labShowSet.setText("模型设置")
        ModelRegion.addWidget(labShowSet)
        self.btnModelSelect = self.create_button(
            CentralWidget, "btnModelSelect", btn_text="模型选择", type="set"
        )
        self.button_add_menu(self.btnModelSelect, ["人像分割", "面部分割", "通用分割", "自定义模型"])
        ModelRegion.addWidget(self.btnModelSelect)  # 模型选择
        SetRegion.addLayout(ModelRegion)
        # 模型信息显示
        ModelInfoRegion = QtWidgets.QHBoxLayout()
        ModelInfoRegion.setObjectName("ModelInfoRegion")
        labModelNameInfo = QtWidgets.QLabel(CentralWidget)
        labModelNameInfo.setObjectName("labModelNameInfo")
        labModelNameInfo.setText("当前模型：")
        ModelInfoRegion.addWidget(labModelNameInfo)
        self.labModelName = QtWidgets.QLabel(CentralWidget)
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
        labFiles = QtWidgets.QLabel(CentralWidget)
        labFiles.setObjectName("labFiles")
        labFiles.setText("数据列表")
        listRegion.addWidget(labFiles)
        self.listFiles = QtWidgets.QListWidget(CentralWidget)
        self.listFiles.setObjectName("listFiles")
        listRegion.addWidget(self.listFiles)
        labelListLab = QtWidgets.QLabel(CentralWidget)
        labelListLab.setObjectName("labelListLab")
        labelListLab.setText("标签类别")
        listRegion.addWidget(labelListLab)
        self.labelListTable = QtWidgets.QTableWidget(CentralWidget)
        self.labelListTable.setObjectName("labelListTable")
        listRegion.addWidget(self.labelListTable)
        self.btnAddClass = self.create_button(
            CentralWidget, "btnAddClass", btn_text="添加标签", type="set"
        )
        listRegion.addWidget(self.btnAddClass)
        # 滑块设置
        SetRegion.addLayout(listRegion)
        ShowSetRegion = QtWidgets.QVBoxLayout()
        ShowSetRegion.setObjectName("ShowSetRegion")
        SegShowRegion = QtWidgets.QHBoxLayout()
        SegShowRegion.setObjectName("SegShowRegion")
        labSeg = QtWidgets.QLabel(CentralWidget)
        labSeg.setObjectName("labSeg")
        labSeg.setText("分割阈值：")
        SegShowRegion.addWidget(labSeg)
        self.labThresh = QtWidgets.QLabel(CentralWidget)
        self.labThresh.setObjectName("labThresh")
        self.labThresh.setText("0.5")
        SegShowRegion.addWidget(self.labThresh)
        SegShowRegion.setStretch(0, 1)
        SegShowRegion.setStretch(1, 10)
        ShowSetRegion.addLayout(SegShowRegion)
        self.sldThresh = QtWidgets.QSlider(CentralWidget)
        self.sldThresh.setMaximum(10)  # 好像只能整数的，这里是扩大了10倍，1 -> 10
        self.sldThresh.setProperty("value", 5)
        self.sldThresh.setOrientation(QtCore.Qt.Horizontal)
        self.sldThresh.setObjectName("sldThresh")
        ShowSetRegion.addWidget(self.sldThresh)
        MaskShowRegion = QtWidgets.QHBoxLayout()
        MaskShowRegion.setObjectName("MaskShowRegion")
        labMask = QtWidgets.QLabel(CentralWidget)
        labMask.setObjectName("labMask")
        labMask.setText("标签透明度：")
        MaskShowRegion.addWidget(labMask)
        self.labOpacity = QtWidgets.QLabel(CentralWidget)
        self.labOpacity.setObjectName("labOpacity")
        self.labOpacity.setText("0.5")
        MaskShowRegion.addWidget(self.labOpacity)
        MaskShowRegion.setStretch(0, 1)
        MaskShowRegion.setStretch(1, 10)
        ShowSetRegion.addLayout(MaskShowRegion)
        self.sldOpacity = QtWidgets.QSlider(CentralWidget)
        self.sldOpacity.setMaximum(10)
        self.sldOpacity.setSingleStep(1)
        self.sldOpacity.setProperty("value", 5)
        self.sldOpacity.setOrientation(QtCore.Qt.Horizontal)
        self.sldOpacity.setObjectName("sldOpacity")
        ShowSetRegion.addWidget(self.sldOpacity)

        PointShowRegion = QtWidgets.QHBoxLayout()
        PointShowRegion.setObjectName("PointShowRegion")
        labPointSzie = QtWidgets.QLabel(CentralWidget)
        labPointSzie.setObjectName("labPointSzie")
        labPointSzie.setText("点击可视化半径：")
        PointShowRegion.addWidget(labPointSzie)
        self.labClickRadius = QtWidgets.QLabel(CentralWidget)
        self.labClickRadius.setObjectName("labClickRadius")
        self.labClickRadius.setText("3")
        PointShowRegion.addWidget(self.labClickRadius)
        ShowSetRegion.addLayout(PointShowRegion)
        self.sldClickRadius = QtWidgets.QSlider(CentralWidget)
        self.sldClickRadius.setMaximum(10)
        self.sldClickRadius.setMinimum(1)
        self.sldClickRadius.setSingleStep(1)
        self.sldClickRadius.setProperty("value", 3)
        self.sldClickRadius.setOrientation(QtCore.Qt.Horizontal)
        self.sldClickRadius.setObjectName("sldClickRadius")
        ShowSetRegion.addWidget(self.sldClickRadius)
        SetRegion.addLayout(ShowSetRegion)
        # # 正负样本选择设置
        # SampleRegion = QtWidgets.QHBoxLayout()
        # SampleRegion.setObjectName("SampleRegion")
        # self.btnPos = self.create_button(CentralWidget, "btnPos", btn_text="正样点", type='set')
        # SampleRegion.addWidget(self.btnPos)
        # self.btnNeg = self.create_button(CentralWidget, "btnNeg", btn_text="负样点", type='set')
        # SampleRegion.addWidget(self.btnNeg)
        # SetRegion.addLayout(SampleRegion)
        # 保存
        self.btnSave = self.create_button(
            CentralWidget, "btnSave", btn_text="保存", type="set", curt="Ctrl+S"
        )
        SetRegion.addWidget(self.btnSave)
        SetRegion.setStretch(2, 10)
        ## dock设置完成
        self.horizontalLayout.addLayout(SetRegion)
        self.DockWidget.setWidget(self.DockRegion)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.DockWidget)

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
    def button_add_menu(self, button, name_list, ist=False):
        menu = QtWidgets.QMenu()
        acts = []
        for name in name_list:
            act = QtWidgets.QAction(name, parent=menu)
            menu.addAction(act)
        button.setMenu(menu)
        button.Menu = menu
        if ist:
            button.setStyleSheet("QPushButton::menu-indicator{image:none;}")  # 不显示小三角
