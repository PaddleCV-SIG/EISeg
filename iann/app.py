import os
import os.path as osp
from functools import partial

from qtpy import QtGui, QtCore, QtWidgets
from qtpy.QtWidgets import QMainWindow, QMessageBox, QTableWidgetItem
from qtpy.QtGui import QImage, QPixmap
from qtpy.QtCore import Qt
import paddle
import cv2

from controller import InteractiveController
from ui import Ui_IANN
from models import models

__appname__ = "IANN"


class APP_IANN(QMainWindow, Ui_IANN):
    def __init__(self, parent=None):
        super(APP_IANN, self).__init__(parent)
        self.setupUi(self)

        # app变量
        self.controller = None
        self.outputDir = None  # 标签保存路径
        self.currIdx = 0  # 标注文件夹时到第几个了
        self.filePaths = []  # 标注文件夹时所有文件路径
        self.labelList = []  # 标签列表(数字，名字，颜色)

        self.labelList = [[1, "人", [0, 0, 0]], [2, "车", [128, 128, 128]]]

        # model = get_deeplab_model(backbone="resnet18", is_ritm=True, cpu_dist_maps=True)
        # para_state_dict = paddle.load("./iann/weight/human_resnet/model.pdparams")
        # model.set_dict(para_state_dict)
        # self.controller = InteractiveController(
        #     model,
        #     predictor_params={"brs_mode": "f-BRS-B"},
        #     update_image_callback=self._update_image,
        # )

        # image = cv2.cvtColor(
        #     cv2.imread("/home/lin/Desktop/dzq.jpg"),
        #     cv2.COLOR_BGR2RGB,
        # )

        # 画布部分
        self.canvas.clickRequest.connect(self.canvas_click)
        self.image = None

        # 消息栏
        self.statusbar.showMessage("模型未加载")

        ## 菜单栏点击
        for menu_act in self.menuBar.actions():
            if menu_act.text() == "文件":
                for ac_act in menu_act.menu().actions():
                    if ac_act.text() == "加载图像":
                        ac_act.triggered.connect(self.openImage)
                    else:
                        ac_act.triggered.connect(self.openFolder)
            elif menu_act.text() == "设置":
                for ac_act in menu_act.menu().actions():
                    if ac_act.text() == "设置保存路径":
                        ac_act.triggered.connect(self.changeOutputDir)
                    else:
                        ac_act.triggered.connect(self.check_click)
            elif menu_act.text() == "帮助":
                for ac_act in menu_act.menu().actions():
                    if ac_act.text() == "快速上手":
                        ac_act.triggered.connect(self.check_click)
                    else:
                        ac_act.triggered.connect(self.check_click)

        ## 工具栏点击
        for tool_act in self.toolBar.actions():
            if tool_act.text() == "完成当前":
                tool_act.triggered.connect(self.finishObject)
            elif tool_act.text() == "清除全部":
                tool_act.triggered.connect(self.undo_all)
            elif tool_act.text() == "撤销":
                tool_act.triggered.connect(self.undo_click)
            elif tool_act.text() == "重做":
                tool_act.triggered.connect(self.check_click)
            elif tool_act.text() == "上一张":
                tool_act.triggered.connect(partial(self.turnImg, -1))
            elif tool_act.text() == "下一张":
                tool_act.triggered.connect(partial(self.turnImg, 1))

        ## 按钮点击
        self.btnSave.clicked.connect(self.saveLabel)  # 保存
        self.listFiles.itemDoubleClicked.connect(self.listClicked)  # list选择 
        self.comboModelSelect.currentIndexChanged.connect(self.changeModel)  # 模型选择

        # 滑动
        self.sldOpacity.valueChanged.connect(self.mask_opacity_changed)
        self.sldClickRadius.valueChanged.connect(self.click_radius_changed)
        self.sldThresh.valueChanged.connect(self.thresh_changed)
        self.refreshLabelList()

    def changeModel(self, idx):
        # TODO: 判断是否有没保存
        # print(
        #     "changing model", self.controller if self.controller is not None else "None"
        # )
        model = models[idx].get_model()
        if self.controller is None:
            self.controller = InteractiveController(
                model,
                predictor_params={"brs_mode": "f-BRS-B"},
                update_image_callback=self._update_image,
            )
        else:
            self.controller.reset_predictor(model)
        self.statusbar.showMessage("已加载模型：" + models[idx].name)

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
            self.tr("%s - 选择待标注图片") % __appname__,
            "/home/lin/Desktop",
            filters,
        )
        if len(file_path) == 0:
            return
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
            self.tr("%s - 选择待标注图片文件夹") % __appname__,
            "/home/lin/Desktop",
            QtWidgets.QFileDialog.ShowDirsOnly
            | QtWidgets.QFileDialog.DontResolveSymlinks,
        )
        if len(self.inputDir) == 0:
            return
        filePaths = os.listdir(self.inputDir)
        exts = QtGui.QImageReader.supportedImageFormats()
        filePaths = [n for n in filePaths if n.split(".")[-1] in exts]
        filePaths = [osp.join(self.inputDir, n) for n in filePaths]
        self.filePaths = filePaths
        self.listFiles.addItems(self.filePaths)
        self.currIdx = 0
        self.turnImg(0)
        # self.loadFile(self.filePaths[0])

    def listClicked(self):
        if self.controller.is_incomplete_mask:
            self.saveLabel()
        toRow = self.listFiles.currentRow()
        delta = toRow - self.currIdx
        self.turnImg(delta)

    def turnImg(self, delta):
        self.currIdx += delta
        if self.currIdx >= len(self.filePaths) or self.currIdx < 0:
            self.currIdx -= delta
            return
        if self.controller.is_incomplete_mask:
            self.saveLabel()
        imagePath = self.filePaths[self.currIdx]
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
            self.tr("%s - 选择标签保存路径") % __appname__,
            osp.dirname(self.imagePath),
            QtWidgets.QFileDialog.ShowDirsOnly
            | QtWidgets.QFileDialog.DontResolveSymlinks,
        )

    def mask_opacity_changed(self):
        self.sldOpacity.textLab.setText(str(self.opacity))
        self._update_image()

    def click_radius_changed(self):
        self.sldClickRadius.textLab.setText(str(self.click_radius))
        self._update_image()

    def thresh_changed(self):
        self.sldThresh.textLab.setText(str(self.seg_thresh))
        self.controller.prob_thresh = self.seg_thresh
        self._update_image()

    def undo_click(self):
        self.controller.undo_click()

    def undo_all(self):
        self.controller.reset_last_object()

    def redo_click(self):
        print("重做功能还没有实现")

    def canvas_click(self, x, y, isLeft):
        if self.controller is None:
            return
        if self.controller.image is None:
            print("image none")
            return
        if x < 0 or y < 0:
            return
        s = self.controller.img_size
        if x > s[0] or y > s[1]:
            return
        self.controller.add_click(x, y, isLeft)

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

    # 当前打开的模型名称或类别更新
    def update_model_name(self):
        self.labModelName.setText(self.sender().text())
        self.check_click()
