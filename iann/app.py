from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QTableWidgetItem
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
import os
import os.path as osp
from functools import partial
import cv2
import paddle
from controller import InteractiveController
from ui import UI_IANN, GraphicsPixmapItem
from model.model import get_hrnet_model, get_deeplab_model


__APPNAME__ = "IANN"


class APP_IANN(QMainWindow, UI_IANN):
    def __init__(self, parent=None):
        super(APP_IANN, self).__init__(parent)
        self.setupUi(self)

        # app变量
        self.outputDir = None
        self.currIdx = 0
        self.fileNames = []
        self.labelList = []  # 名字，颜色，数字
        self.labelList = [[1, "人", [0, 0, 0]], [2, "车", [128, 128, 128]]]

        # 模型部分
        model = get_deeplab_model(backbone="resnet18", is_ritm=True, cpu_dist_maps=True)
        para_state_dict = paddle.load(
            "iann/weight/human_resnet/model.pdparams"
        )
        model.set_dict(para_state_dict)
        self.controller = InteractiveController(
            model,
            predictor_params={"brs_mode": "f-BRS-B"},
            update_image_callback=self._update_image,
        )

        # 画布部分
        self.view.clickRequest.connect(self.canvas_click)
        self.image = None

        ## 信号
        self.actLoadImage.triggered.connect(self.openImage)  # 打开图像
        self.actOpenFolder.triggered.connect(self.openFolder)  # 打开文件夹
        self.actUndo.triggered.connect(self.undo_click)  # 撤销
        self.actRedo.triggered.connect(self.check_click)  # 重做
        self.actClear.triggered.connect(self.undo_all)  # 撤销全部
        self.menuAbout.triggered.connect(self.check_click)  # 关于
        self.actFinish.triggered.connect(self.finishObject)  # 保存当前
        self.actPrevImg.triggered.connect(partial(self.turnImg, -1))  # 上一张图
        self.actNextImg.triggered.connect(partial(self.turnImg, 1))  # 下一张图
        self.btnSave.clicked.connect(self.saveLabel)  # 保存
        self.btnAddClass.clicked.connect(self.check_click)  # 添加标签
        self.actSave.triggered.connect(self.changeOutputDir)  # 保存路径
        self.listFiles.itemDoubleClicked.connect(self.listClicked)

        # 选择模型
        for action in self.btnModelSelect.Menu.actions():
            action.triggered.connect(self.update_model_name)
        
        # 分别滑动三个滑动滑块
        self.sldOpacity.valueChanged.connect(self.mask_opacity_changed)
        self.sldClickRadius.valueChanged.connect(self.click_radius_changed)
        self.sldThresh.valueChanged.connect(self.thresh_changed)

        self.refreshLabelList()

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

    def refreshLabelList(self):
        table = self.labelListTable
        # TODO: 添加表头
        table.clearContents()
        table.setRowCount(len(self.labelList))
        table.setColumnCount(3)
        for idx, lab in enumerate(self.labelList):
            table.setItem(idx, 0, QTableWidgetItem(str(lab[0])))
            table.setItem(idx, 1, QTableWidgetItem(lab[1]))
            c = lab[2]
            table.setItem(idx, 2, QTableWidgetItem())
            table.item(idx, 2).setBackground(QtGui.QColor(c[0], c[1], c[2]))

    def addLabel(self):
        pass

    def openImage(self):
        formats = [
            "*.{}".format(fmt.data().decode())
            for fmt in QtGui.QImageReader.supportedImageFormats()
        ]
        filters = self.tr("Image & Label files (%s)") % " ".join(formats)
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            self.tr("%s - 选择待标注图片") % __APPNAME__,
            "/home/lin/Desktop",
            filters,
        )
        if len(file_path) == 0:
            return
        # 显示
        self.createPixmapItem(QPixmap(file_path), self.position())
        self.loadFile(file_path)
        self.imagePath = file_path

    def loadFile(self, path):
        # TODO: 读取标签
        if len(path) == 0 or not osp.exists(path):
            return
        image = cv2.cvtColor(
            cv2.imread(path),
            cv2.COLOR_BGR2RGB,
        )
        self.controller.set_image(image)

    def openFolder(self):
        self.inputDir = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            self.tr("%s - 选择待标注图片文件夹") % __APPNAME__,
            "/home/lin/Desktop",
            QtWidgets.QFileDialog.ShowDirsOnly
            | QtWidgets.QFileDialog.DontResolveSymlinks,
        )
        if len(self.inputDir) == 0:
            return
        fileNames = os.listdir(self.inputDir)
        exts = QtGui.QImageReader.supportedImageFormats()
        fileNames = [n for n in fileNames if n.split(".")[-1] in exts]
        fileNames = [osp.join(self.inputDir, n) for n in fileNames]
        self.fileNames = fileNames
        self.listFiles.addItems(self.fileNames)
        self.currIdx = 0
        self.turnImg(0)
        # self.loadFile(self.fileNames[0])

    def listClicked(self):
        if self.controller.is_incomplete_mask:
            self.saveLabel()
        toRow = self.listFiles.currentRow()
        delta = toRow - self.currIdx
        self.turnImg(delta)

    def turnImg(self, delta):
        self.currIdx += delta
        if self.currIdx >= len(self.fileNames) or self.currIdx < 0:
            self.currIdx -= delta
            return
        if self.controller.is_incomplete_mask:
            self.saveLabel()
        imagePath = self.fileNames[self.currIdx]
        self.loadFile(imagePath)
        self.imagePath = imagePath
        self.listFiles.setCurrentRow(self.currIdx)

    def finishObject(self):
        self.controller.finish_object()

    def saveLabel(self):
        if self.controller.image is None:
            return

        if self.controller.is_incomplete_mask:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("保存最后一个目标？")
            msg.setText("最后一个目标尚未完成标注，是否进行保存？")
            # msg.setInformativeText("")
            # msg.setDetailedText("The details are as follows:")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
            # msg.buttonClicked.connect()
            res = msg.exec_()
            print(QMessageBox.Yes, res)
            if res == QMessageBox.Yes:
                print("Yes")
                self.finishObject()
            else:
                return

        if not self.outputDir:
            filters = self.tr("Label files (*.png)")
            # BUG: 默认打开路径有问题
            dlg = QtWidgets.QFileDialog(
                self, "保存标签文件路径", osp.dirname(self.imagePath), filters
            )
            dlg.setDefaultSuffix("png")
            dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
            dlg.setOption(QtWidgets.QFileDialog.DontConfirmOverwrite, False)
            dlg.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, False)
            savePath, _ = dlg.getSaveFileName(
                self,
                self.tr("选择标签文件保存路径"),
                osp.basename(self.imagePath).split(".")[0] + ".png",
            )
            if (
                savePath is None
                or len(savePath) == 0
                or not osp.exists(osp.dirname(savePath))
            ):
                return
        else:
            savePath = osp.join(
                self.outputDir, osp.basename(self.imagePath).split(".")[0] + ".png"
            )
        print(self.controller.result_mask.shape)
        cv2.imwrite(savePath, self.controller.result_mask)

    def changeOutputDir(self):
        self.outputDir = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            self.tr("%s - 选择标签保存路径") % __APPNAME__,
            osp.dirname(self.imagePath),
            QtWidgets.QFileDialog.ShowDirsOnly
            | QtWidgets.QFileDialog.DontResolveSymlinks,
        )

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

    def canvas_click(self, x, y, isLeft):
        if self.controller.image is None:
            return
        if x < 0 or y < 0:
            return
        s = self.controller.img_size
        if x > s[0] or y > s[1]:
            return
        self.controller.add_click(x, y, isLeft=="left")

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
        # TODO: 研究是否有类似swap的更高效方式
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