from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtGui import QImage, QPixmap
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
import paddle
import cv2
import os

from controller import InteractiveController
from ui import Ui_IANN, GraphicsPixmapItem
from model import get_hrnet_model, get_deeplab_model


class APP_IANN(QMainWindow, Ui_IANN):
    def __init__(self, parent=None):
        super(APP_IANN, self).__init__(parent)
        self.setupUi(self)
        self.use_img = False

        model = get_deeplab_model(backbone="resnet18", is_ritm=True, cpu_dist_maps=True)
        para_state_dict = paddle.load(
            "weight/human_resnet/model.pdparams"
        )
        model.set_dict(para_state_dict)
        self.controller = InteractiveController(
            model,
            predictor_params={"brs_mode": "f-BRS-B"},
            update_image_callback=self._update_image,
        )

        # 画布部分
        # self.canvas.mousePressEvent = self.canvas_click
        self.view.clickRequest.connect(self.canvas_click)
        self.image = None
        self.item = None

        ## 信号
        self.btnOpenImage.clicked.connect(self.openImage)  # 打开图像
        self.btnOpenFolder.clicked.connect(self.check_click)  # 打开文件夹
        self.btnUndo.clicked.connect(self.undo_click)  # 撤销
        self.btnRedo.clicked.connect(self.check_click)  # 重做
        self.btnUndoAll.clicked.connect(self.undo_all)  # 撤销全部
        self.btnAbout.clicked.connect(self.check_click)  # 关于

        # 细粒度（这种可以通过sender的text来知道哪个键被点击了）
        for action in self.btnScale.Menu.actions():
            action.triggered.connect(self.check_click)
        # 帮助
        for action in self.btnHelp.Menu.actions():
            action.triggered.connect(self.check_click)
        self.btnPrevImg.clicked.connect(self.check_click)  # 上一张图
        self.btnNextImg.clicked.connect(self.check_click)  # 下一张图
        # 选择模型
        for action in self.btnModelSelect.Menu.actions():
            action.triggered.connect(self.update_model_name)
        self.listLabel.clicked.connect(self.check_click)  # 数据列表选择（用row可以获取点击的行数）
        self.listClass.clicked.connect(self.check_click)  # 标签选择
        self.btnAddClass.clicked.connect(self.check_click)  # 添加标签
        # 分别滑动三个滑动滑块
        self.sldOpacity.valueChanged.connect(self.mask_opacity_changed)
        self.sldClickRadius.valueChanged.connect(self.click_radius_changed)
        self.sldThresh.valueChanged.connect(self.thresh_changed)
        self.btnSave.clicked.connect(self.check_click)  # 保存

    def openImage(self):
        self.path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "选取图像", os.getcwd(), \
                       "Image Files (*.bmp *.jpg *.png)")   # 设置文件扩展名过滤，用双分号间隔
        if self.path:
            self.image = cv2.cvtColor(
                cv2.imread(self.path),
                cv2.COLOR_BGR2RGB,
            )
            # 显示
            self.item = self.createPixmapItem(QPixmap(self.path), self.position())
            # 控制器
            self.controller.set_image(self.image)
            self.use_img = True  # 已经打开图像了

    def position(self):
        point = self.mapFromGlobal(QtGui.QCursor.pos())
        if not self.view.geometry().contains(point):
            coord = random.randint(36, 144)
            point = Qt.QPoint(coord, coord)
        else:
            if point == self.prevPoint:
                point += Qt.QPoint(self.addOffset, self.addOffset)
                self.addOffset += 5
            else:
                self.addOffset = 5
                self.prevPoint = point
        return self.view.mapToScene(point)

    def createPixmapItem(self, pixmap, position, matrix=QtGui.QTransform()):
        item = GraphicsPixmapItem(pixmap)
        item.setFlags(QtWidgets.QGraphicsItem.ItemIsSelectable|
                      QtWidgets.QGraphicsItem.ItemIsMovable)
        item.setPos(position)
        item.setTransform(matrix)
        self.scene.clearSelection()
        self.scene.addItem(item)
        item.setSelected(True)
        return item

    def mask_opacity_changed(self):
        self.labOpacity.setText(str(self.opacity))
        self._update_image()

    def click_radius_changed(self):
        self.labClickRadius.setText(str(self.click_radius))
        self._update_image()

    def thresh_changed(self):
        self.labThresh.setText(str(self.seg_thresh))
        self.controller.prob_thresh = self.seg_thresh
        self._update_image()

    def undo_click(self):
        self.controller.undo_click()

    def undo_all(self):
        self.controller.reset_last_object()

    def redo_click(self):
        print("重做功能还没有实现")

    def canvas_click(self, x, y, mouse_in):
        if self.use_img:
            if x < 0 or y < 0:
                return
            s = self.controller.img_size
            if x > s[0] or y > s[1]:
                return
            # 样本点选择
            if mouse_in != "middle":
                is_positive = True if mouse_in == "left" else False
                self.controller.add_click(x, y, is_positive)

    @property
    def opacity(self):
        return self.sldOpacity.value() / 10

    @property
    def click_radius(self):
        return self.sldClickRadius.value()

    @property
    def seg_thresh(self):
        return self.sldThresh.value() / 10

    def _update_image(self, reset_canvas=False):
        image = self.controller.get_visualization(
            alpha_blend=self.opacity,
            click_radius=self.click_radius,
        )
        height, width, channel = image.shape
        bytesPerLine = 3 * width
        image = QImage(image.data, width, height, bytesPerLine, QImage.Format_RGB888)
        self.scene.addPixmap(QPixmap(image))
        self.scene.removeItem(self.scene.items()[1])

    # 确认点击
    def check_click(self):
        print(self.sender().text())

    # 滑块数值与标签数值同步
    def slider_2_label(self):
        slider = self.sender()
        name = slider.objectName()
        if name == "sldMask":
            self.labMaskShow.setText(str(slider.value() / 10.0))
        elif name == "sldSeg":
            self.labSegShow.setText(str(slider.value() / 10.0))
        else:
            self.labPointSizeShow.setText(str(slider.value()))

    # 当前打开的模型名称或类别更新
    def update_model_name(self):
        self.labModelName.setText(self.sender().text())
        self.check_click()
