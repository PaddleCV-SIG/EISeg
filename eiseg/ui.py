from enum import Enum
from functools import partial

from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QGraphicsView

from models import models
from eiseg import __APPNAME__
from util import Instructions


class GripItem(QtWidgets.QGraphicsPathItem):
    circle = QtGui.QPainterPath()
    circle.addEllipse(QtCore.QRectF(-3, -3, 6, 6))
    square = QtGui.QPainterPath()
    square.addRect(QtCore.QRectF(-3, -3, 6, 6))

    def __init__(self, annotation_item, index):
        super(GripItem, self).__init__()
        self.m_annotation_item = annotation_item
        self.m_index = index

        self.setPath(GripItem.circle)
        self.setBrush(QtGui.QColor("green"))
        self.setPen(QtGui.QPen(QtGui.QColor("green"), 2))
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(11)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

    def hoverEnterEvent(self, ev):
        self.setPath(GripItem.square)
        self.setBrush(QtGui.QColor("red"))
        self.m_annotation_item.item_hovering = True
        super(GripItem, self).hoverEnterEvent(ev)

    def hoverLeaveEvent(self, ev):
        self.setPath(GripItem.circle)
        self.setBrush(QtGui.QColor("green"))
        self.m_annotation_item.item_hovering = False
        super(GripItem, self).hoverLeaveEvent(ev)

    def mouseReleaseEvent(self, ev):
        self.setSelected(False)
        super(GripItem, self).mouseReleaseEvent(ev)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemPositionChange and self.isEnabled():
            self.m_annotation_item.movePoint(self.m_index, value)
        return super(GripItem, self).itemChange(change, value)


class PolygonAnnotation(QtWidgets.QGraphicsPolygonItem):
    def __init__(self, parent=None):
        super(PolygonAnnotation, self).__init__(parent)
        self.item_hovering = False
        self.polygon_hovering = False
        self.m_points = []
        self.setZValue(10)
        self.setPen(QtGui.QPen(QtGui.QColor("green"), 2))
        self.setAcceptHoverEvents(True)

        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)

        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        self.m_items = []

    def number_of_points(self):
        return len(self.m_items)

    def addPoint(self, p):
        self.m_points.append(p)
        self.setPolygon(QtGui.QPolygonF(self.m_points))
        item = GripItem(self, len(self.m_points) - 1)
        self.scene().addItem(item)
        self.m_items.append(item)
        item.setPos(p)

    def removeLastPoint(self):
        if self.m_points:
            self.m_points.pop()
            self.setPolygon(QtGui.QPolygonF(self.m_points))
            it = self.m_items.pop()
            self.scene().removeItem(it)
            del it

    def movePoint(self, i, p):
        if 0 <= i < len(self.m_points):
            self.m_points[i] = self.mapFromScene(p)
            self.setPolygon(QtGui.QPolygonF(self.m_points))

    def move_item(self, index, pos):
        if 0 <= index < len(self.m_items):
            item = self.m_items[index]
            item.setEnabled(False)
            item.setPos(pos)
            item.setEnabled(True)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemPositionHasChanged:
            for i, point in enumerate(self.m_points):
                self.move_item(i, self.mapToScene(point))
        return super(PolygonAnnotation, self).itemChange(change, value)

    def hoverEnterEvent(self, ev):
        self.polygon_hovering = True
        self.setBrush(QtGui.QColor(255, 0, 0, 100))
        super(PolygonAnnotation, self).hoverEnterEvent(ev)

    def hoverLeaveEvent(self, ev):
        self.polygon_hovering = False
        self.setBrush(QtGui.QBrush(QtCore.Qt.NoBrush))
        super(PolygonAnnotation, self).hoverLeaveEvent(ev)


class AnnotationScene(QtWidgets.QGraphicsScene):
    clickRequest = QtCore.Signal(int, int, bool)

    def __init__(self, parent=None):
        super(AnnotationScene, self).__init__(parent)
        self.current_instruction = Instructions.No_Instruction
        self.polygon_item = PolygonAnnotation()

        self.addItem(self.polygon_item)

    def setCurrentInstruction(self, instruction=Instructions.Polygon_Instruction):
        self.current_instruction = instruction

    def mousePressEvent(self, ev):
        pos = ev.scenePos()
        print(self.current_instruction, self.polygon_item.item_hovering)
        if (
            self.current_instruction == Instructions.No_Instruction
            and not self.polygon_item.item_hovering
            and not self.polygon_item.polygon_hovering
        ):
            if ev.buttons() in [Qt.LeftButton, Qt.RightButton]:
                self.clickRequest.emit(pos.x(), pos.y(), ev.buttons() == Qt.LeftButton)

        elif self.current_instruction == Instructions.Polygon_Instruction:
            self.polygon_item.removeLastPoint()
            self.polygon_item.addPoint(ev.scenePos())
            # movable element
            self.polygon_item.addPoint(ev.scenePos())
        super(AnnotationScene, self).mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if self.current_instruction == Instructions.Polygon_Instruction:
            self.polygon_item.movePoint(
                self.polygon_item.number_of_points() - 1, ev.scenePos()
            )
        super(AnnotationScene, self).mouseMoveEvent(ev)


class AnnotationView(QGraphicsView):
    def __init__(self, *args):
        super(AnnotationView, self).__init__(*args)
        self.setRenderHints(
            QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform
        )
        self.setMouseTracking(True)
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setResizeAnchor(QGraphicsView.NoAnchor)
        self.point = QtCore.QPoint(0, 0)
        self.middle_click = False
        self.zoom_all = 1

    def wheelEvent(self, ev):
        if ev.modifiers() & QtCore.Qt.ControlModifier:
            print(ev.angleDelta().x(), ev.angleDelta().y())
            zoom = 1 + ev.angleDelta().y() / 2880
            self.zoom_all *= zoom
            oldPos = self.mapToScene(ev.pos())
            if self.zoom_all >= 0.02 and self.zoom_all <= 50:  # 限制缩放的倍数
                self.scale(zoom, zoom)
            newPos = self.mapToScene(ev.pos())
            delta = newPos - oldPos
            self.translate(delta.x(), delta.y())
            ev.ignore()
        else:
            super(AnnotationView, self).wheelEvent(ev)

    def mouseMoveEvent(self, ev):
        if self.middle_click and (
            self.horizontalScrollBar().isVisible()
            or self.verticalScrollBar().isVisible()
        ):
            # 放大到出现滚动条才允许拖动，避免出现抖动
            self._endPos = ev.pos() / self.zoom_all - self._startPos / self.zoom_all
            # 这儿不写为先减后除，这样会造成速度不一致
            self.point = self.point + self._endPos
            self._startPos = ev.pos()
            print("move", self._endPos.x(), self._endPos.y())
            self.translate(self._endPos.x(), self._endPos.y())
        super(AnnotationView, self).mouseMoveEvent(ev)

    def mousePressEvent(self, ev):
        if ev.buttons() == Qt.MiddleButton:
            self.middle_click = True
            self._startPos = ev.pos()
        super(AnnotationView, self).mousePressEvent(ev)

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MiddleButton:
            self.middle_click = False
        super(AnnotationView, self).mouseReleaseEvent(ev)


class Ui_Help(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowTitle("Help")
        Dialog.resize(650, 560)
        Dialog.setStyleSheet("background-color: rgb(255, 255, 255);")
        horizontalLayout = QtWidgets.QHBoxLayout(Dialog)
        horizontalLayout.setObjectName("horizontalLayout")
        label = QtWidgets.QLabel(Dialog)
        label.setText("")
        # label.setPixmap(QtGui.QPixmap("EISeg/resources/shortkey.jpg"))
        label.setObjectName("label")
        horizontalLayout.addWidget(label)
        QtCore.QMetaObject.connectSlotsByName(Dialog)


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
        self.statusbar.addPermanentWidget(self.show_logo("eiseg/resource/Paddle.png"))
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
        # self.scene = QtWidgets.QGraphicsScene()
        self.scene = AnnotationScene()

        QtWidgets.QShortcut(
            QtCore.Qt.Key_Escape,
            self,
            activated=partial(
                self.scene.setCurrentInstruction, Instructions.No_Instruction
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
        self.dockWorker.setWindowTitle("工作区")
        self.dockWorker.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFloatable
            | QtWidgets.QDockWidget.DockWidgetMovable
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
        labShowSet = self.create_text(CentralWidget, "labShowSet", "网络选择")
        ModelRegion.addWidget(labShowSet)
        combo = QtWidgets.QComboBox(self)
        # for model in models:
        #     combo.addItem(model.name)
        # 网络参数
        combo.addItems([m.name for m in models])
        self.comboModelSelect = combo
        ModelRegion.addWidget(self.comboModelSelect)  # 模型选择
        self.btnParamsSelect = p_create_button(
            "btnParamsLoad", "加载网络参数", "eiseg/resource/Model.png", "Ctrl+D"
        )
        ModelRegion.addWidget(self.btnParamsSelect)  # 模型选择
        SetRegion.addLayout(ModelRegion)
        SetRegion.setStretch(0, 1)
        # 数据列表
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
        # 自适应填充
        self.labelListTable.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents
        )
        self.labelListTable.verticalHeader().hide()
        self.labelListTable.setColumnWidth(0, 10)
        # self.labelListTable.setMinimumWidth()
        self.labelListTable.setObjectName("labelListTable")
        listRegion.addWidget(self.labelListTable)
        self.btnAddClass = p_create_button(
            "btnAddClass", "添加标签", "eiseg/resource/Label.png"
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
            "btnSave", "保存", "eiseg/resource/Save.png", "Ctrl+S"
        )
        SetRegion.addWidget(self.btnSave)
        SetRegion.setStretch(3, 1)
        # dock设置完成
        horizontalLayout.addLayout(SetRegion)
        self.dockWorker.setWidget(DockRegion)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.dockWorker)
        ## -----
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    ## 创建文本
    def create_text(self, parent, text_name=None, text_text=None):
        text = QtWidgets.QLabel(parent)
        if text_name is not None:
            text.setObjectName(text_name)
        if text_text is not None:
            text.setText(text_text)
        return text

    ## 创建按钮
    def create_button(self, parent, btn_name, btn_text, ico_path=None, curt=None):
        # 创建和设置按钮
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
        if ico_path is not None:
            btn.setIcon(QtGui.QIcon(ico_path))
        btn.setText(btn_text)
        if curt is not None:
            btn.setShortcut(curt)
        return btn

    ## 添加动作
    # def add_action(self, parent, act_name, act_text="", ico_path=None, short_cut=None):
    #     act = QtWidgets.QAction(parent)
    #     if ico_path is not None:
    #         icon = QtGui.QIcon()
    #         icon.addPixmap(QtGui.QPixmap(ico_path), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    #         act.setIcon(icon)
    #     act.setObjectName(act_name)
    #     act.setText(act_text)
    #     if short_cut is not None:
    #         act.setShortcut(short_cut)
    #     return act

    ## 创建菜单按钮
    # def add_menu(self, parent, menu_name, menu_text, acts=None):
    #     menu = QtWidgets.QMenu(parent)
    #     menu.setObjectName(menu_name)
    #     menu.setTitle(menu_text)
    #     if acts is not None:
    #         for act in acts:
    #             new_act = self.add_action(parent, act[0], act[1], act[2], act[3])
    #             menu.addAction(new_act)
    #     return menu

    ## 创建菜单栏
    # def create_menubar(self, parent, menus):
    #     menuBar = QtWidgets.QMenuBar(parent)
    #     menuBar.setGeometry(QtCore.QRect(0, 0, 800, 26))
    #     menuBar.setObjectName("menuBar")
    #     for menu in menus:
    #         menuBar.addAction(menu.menuAction())
    #     return menuBar

    # ## 创建工具栏
    # def create_toolbar(self, parent, acts):
    #     toolBar = QtWidgets.QToolBar(parent)
    #     sizePolicy = QtWidgets.QSizePolicy(
    #         QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum
    #     )
    #     sizePolicy.setHorizontalStretch(0)
    #     sizePolicy.setVerticalStretch(0)
    #     sizePolicy.setHeightForWidth(toolBar.sizePolicy().hasHeightForWidth())
    #     toolBar.setSizePolicy(sizePolicy)
    #     toolBar.setMinimumSize(QtCore.QSize(0, 33))
    #     toolBar.setMovable(True)
    #     toolBar.setAllowedAreas(QtCore.Qt.BottomToolBarArea | QtCore.Qt.TopToolBarArea)
    #     toolBar.setObjectName("toolBar")
    #     for act in acts:
    #         new_act = self.add_action(parent, act[0], act[1], act[2], act[3])
    #         toolBar.addAction(new_act)
    #     return toolBar

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
        Region = QtWidgets.QHBoxLayout()
        lab = self.create_text(parent, None, text)
        Region.addWidget(lab)
        labShow = self.create_text(parent, text_name, str(default_value * text_rate))
        Region.addWidget(labShow)
        Region.setStretch(0, 1)
        Region.setStretch(1, 10)
        sld = QtWidgets.QSlider(parent)
        sld.setMaximum(max_value)  # 好像只能整数的，这里是扩大了10倍，1 . 10
        sld.setProperty("value", default_value)
        sld.setOrientation(QtCore.Qt.Horizontal)
        sld.setObjectName(sld_name)
        sld.setStyleSheet(
            """
            QSlider::sub-page:horizontal {
                background: #9999F1
            }
            QSlider::handle:horizontal
            {
                background: #3334E3;
                width: 12px;
                border-radius: 4px;
            }
            """
        )
        sld.textLab = labShow
        return sld, Region
