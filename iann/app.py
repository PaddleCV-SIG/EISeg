import os
import os.path as osp
from functools import partial

from qtpy import QtGui, QtCore, QtWidgets
from qtpy.QtWidgets import QMainWindow, QMessageBox, QTableWidgetItem
from qtpy.QtGui import QImage, QPixmap
from qtpy.QtCore import Qt
import paddle
import cv2
import numpy as np

from controller import InteractiveController
from ui import Ui_IANN, Ui_Help
from models import models
import util

__appname__ = "IANN"


class APP_IANN(QMainWindow, Ui_IANN):
    def __init__(self, parent=None):
        super(APP_IANN, self).__init__(parent)
        self.setupUi(self)
        # 显示帮助
        self.help_dialog = QtWidgets.QDialog()
        help_ui = Ui_Help()
        help_ui.setupUi(self.help_dialog)

        # app变量
        self.controller = None
        self.outputDir = None  # 标签保存路径
        self.labelFiles = None  # 保存所有从outputdir发现的标签文件路径
        self.currIdx = 0  # 标注文件夹时到第几个了
        self.filePaths = []  # 标注文件夹时所有文件路径
        self.labelList = []  # 标签列表(数字，名字，颜色)

        self.labelList = [[1, "人", [0, 0, 0]], [2, "车", [128, 128, 128]]]

        # 画布部分
        self.canvas.clickRequest.connect(self.canvasClick)
        self.image = None

        # 消息栏
        self.statusbar.showMessage("模型未加载")

        self.initActions()

        ## 按钮点击
        self.btnSave.clicked.connect(self.saveLabel)  # 保存
        self.listFiles.itemDoubleClicked.connect(self.listClicked)  # list选择
        self.comboModelSelect.currentIndexChanged.connect(self.changeModel)  # 模型选择
        self.btnAddClass.clicked.connect(self.addLabel)

        # 滑动
        self.sldOpacity.valueChanged.connect(self.maskOpacityChanged)
        self.sldClickRadius.valueChanged.connect(self.clickRadiusChanged)
        self.sldThresh.valueChanged.connect(self.threshChanged)
        self.refreshLabelList()

        # TODO: 打开上次关软件时用的模型
        # TODO: 在ui展示后再加载模型

    def toBeImplemented(self):
        self.statusbar.showMessage("功能尚在开发")
        pass

    def initActions(self):
        def menu(title, actions=None):
            menu = self.menuBar().addMenu(title)
            if actions:
                util.addActions(menu, actions)
            return menu

        action = partial(util.newAction, self)
        shortcuts = {
            "turn_next": "F",
            "turn_prev": "S",
            "open_image": "Ctrl+A",
            "open_folder": "Shift+A",
            "change_output_dir": "Shift+Z",
            "finish_object": "Space",
            "clear": "Ctrl+Shift+Z",
            "undo": "Ctrl+Z",
            "redo": "Ctrl+Y",
        }

        turn_next = action(
            self.tr("&下一张"),
            partial(self.turnImg, 1),
            shortcuts["turn_next"],
            "next",
            self.tr("翻到下一张图片"),
        )
        turn_prev = action(
            self.tr("&上一张"),
            partial(self.turnImg, -1),
            shortcuts["turn_prev"],
            "prev",
            self.tr("翻到上一张图片"),
        )
        open_image = action(
            self.tr("&打开图像"),
            self.openImage,
            shortcuts["open_image"],
            # TODO: 搞个图
            "",
            self.tr("打开一张图像进行标注"),
        )
        open_folder = action(
            self.tr("&打开文件夹"),
            self.openFolder,
            shortcuts["open_folder"],
            # TODO: 搞个图
            "",
            self.tr("打开一个文件夹下所有的图像进行标注"),
        )
        change_output_dir = action(
            self.tr("&改变标签保存路径"),
            self.changeOutputDir,
            shortcuts["change_output_dir"],
            # TODO: 搞个图
            "",
            self.tr("打开一个文件夹下所有的图像进行标注"),
        )
        quick_start = action(
            self.tr("&快速上手"),
            self.toBeImplemented,
            None,
            # TODO: 搞个图
            "",
            self.tr("快速上手介绍"),
        )
        about = action(
            self.tr("&关于软件"),
            self.toBeImplemented,
            None,
            # TODO: 搞个图
            "",
            self.tr("关于这个软件和开发团队"),
        )
        grid_ann = action(
            self.tr("&N^2宫格标注"),
            self.toBeImplemented,
            None,
            # TODO: 搞个图
            "",
            self.tr("使用N^2宫格进行细粒度标注"),
        )
        finish_object = action(
            self.tr("&完成当前目标"),
            self.finishObject,
            shortcuts["finish_object"],
            "finish",
            self.tr("完成当前目标的标注"),
        )
        clear = action(
            self.tr("&清除所有标注"),
            self.clearMask,
            shortcuts["clear"],
            "clear",
            self.tr("清除所有标注信息"),
        )
        undo = action(
            self.tr("&撤销"),
            self.undoClick,
            shortcuts["undo"],
            "undo",
            self.tr("撤销一次点击"),
        )
        redo = action(
            self.tr("&重做"),
            self.toBeImplemented,
            shortcuts["redo"],
            "redo",
            self.tr("重做一次点击"),
        )

        # TODO: 改用manager
        self.actions = util.struct(
            turn_next=turn_next,
            turn_prev=turn_prev,
            open_image=open_image,
            open_folder=open_folder,
            fileMenu=(
                open_image,
                open_folder,
                change_output_dir,
                None,
                turn_prev,
                turn_next,
            ),
            helpMenu=(quick_start, about),
            labelMenu=(grid_ann,),
            toolBar=(finish_object, clear, undo, redo, turn_prev, turn_next),
        )
        menu("文件", self.actions.fileMenu)
        menu("标注", self.actions.labelMenu)
        menu("帮助", self.actions.helpMenu)
        util.addActions(self.toolBar, self.actions.toolBar)

    def changeOutputDir(self, dir=None):
        if dir is not None:
            outputDir = QtWidgets.QFileDialog.getExistingDirectory(
                self,
                self.tr("%s - 选择标签文件夹") % __appname__,
                "/home/aistudio/git/paddle/iann",
                QtWidgets.QFileDialog.ShowDirsOnly
                | QtWidgets.QFileDialog.DontResolveSymlinks,
            )
        if len(outputDir) == 0:
            return

        labelFiles = os.listdir(outputDir)
        exts = QtGui.QImageReader.supportedImageFormats()
        self.labelFiles = [
            osp.join(outputDir, n) for n in labelFiles if n.split(".")[-1] in exts
        ]
        self.outputDir = outputDir

    def changeModel(self, idx):
        # TODO: 设置gpu还是cpu运行
        self.statusbar.showMessage(f"正在加载 {models[idx].name} 模型", 5000)
        model = models[idx].get_model()
        if self.controller is None:
            self.controller = InteractiveController(
                model,
                predictor_params={"brs_mode": "f-BRS-B"},
                update_image_callback=self._update_image,
            )
            # 这里如果直接加载模型会报错，先判断有没有图像
            if self.image is not None:
                self.controller.set_image(self.image)
        else:
            self.controller.reset_predictor(model)

        self.statusbar.showMessage(f"{ models[idx].name}模型加载完成", 5000)

    def addLabel(self):
        table = self.labelListTable
        table.insertRow(table.rowCount())
        idx = table.rowCount() - 1
        print(idx)
        numberItem = QTableWidgetItem(str(idx + 1))
        numberItem.setFlags(QtCore.Qt.ItemIsEnabled)
        table.setItem(idx, 0, numberItem)
        table.setItem(idx, 1, QTableWidgetItem())
        c = [255, 255, 255]
        colorItem = QTableWidgetItem()
        colorItem.setBackground(QtGui.QColor(c[0], c[1], c[2]))
        colorItem.setFlags(QtCore.Qt.ItemIsEnabled)
        table.setItem(idx, 2, colorItem)
        self.labelList.append([idx + 1, "", [255, 255, 255]])

    def refreshLabelList(self):
        table = self.labelListTable
        table.clearContents()
        table.setRowCount(len(self.labelList))
        table.setColumnCount(3)
        for idx, lab in enumerate(self.labelList):
            numberItem = QTableWidgetItem(str(lab[0]))
            numberItem.setFlags(QtCore.Qt.ItemIsEnabled)
            table.setItem(idx, 0, numberItem)
            table.setItem(idx, 1, QTableWidgetItem(lab[1]))
            c = lab[2]
            colorItem = QTableWidgetItem()
            colorItem.setBackground(QtGui.QColor(c[0], c[1], c[2]))
            colorItem.setFlags(QtCore.Qt.ItemIsEnabled)
            table.setItem(idx, 2, colorItem)

        for idx in range(2):
            table.resizeColumnToContents(idx)

        def changeLabelColor(row, col):
            print(row, col)
            if col != 2:
                return
            color = QtWidgets.QColorDialog.getColor()
            # BUG: 判断颜色没变
            print(color.getRgb())
            table.item(row, col).setBackground(color)
            self.labelList[row][2] = color.getRgb()[:3]
            if self.controller:
                self.controller.label_list = self.labelList

        table.cellDoubleClicked.connect(changeLabelColor)

        def cellClicked(row, col):
            print("cell clicked", row, col)
            for idx in range(3):
                table.item(row, idx).setSelected(True)
            if self.controller:
                print(int(table.item(row, 0).text()))
                self.controller.change_label_num(int(table.item(row, 0).text()))
                self.controller.label_list = self.labelList

        table.cellClicked.connect(cellClicked)

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
        if len(path) == 0 or not osp.exists(path):
            return
        # TODO: 在不同平台测试含中文路径
        image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), 1)
        image = image[:, :, ::-1]  # BGR转RGB
        self.image = image
        imgName = osp.basename(path).split(".")[0]
        # TODO: 专门搞一个getlabel的方法
        # if self.outputDir:
        #     for labelName in self.labelFiles:
        #         if osp.basename(labelName).split(".")[0] == imgName:
        #             label = cv2.imdecode(np.fromfile(labelName, dtype=np.uint8), 1)
        #             print(label.shape)
        #             break
        if self.controller:
            self.controller.set_image(self.image)
        else:
            self.changeModel(0)

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
            self.statusbar.showMessage(f"没有{'后一张'if delta==1 else '前一张'}图片")
            return
        if not self.controller:
            self.changeModel(0)
        if self.controller.is_incomplete_mask:
            self.saveLabel()
        imagePath = self.filePaths[self.currIdx]
        self.loadFile(imagePath)
        if self.controller.is_incomplete_mask:
            self.saveLabel()
        # self.loadFile(imagePath)放在前面，不然不先加载模型找不到self.controller
        # 不过这里我不清楚逻辑上是否应该if判断在前，需要修改的话再来修改
        self.imagePath = imagePath
        self.listFiles.setCurrentRow(self.currIdx)

    def finishObject(self):
        if self.image is None:
            return
        self.controller.finish_object()

    def saveLabel(self):
        if self.controller.image is None:
            return

        if self.controller.is_incomplete_mask:
            # TODO: 如果没选，直接esc，什么也不做
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
            # osp.dirname(self.imagePath),
            ".",
            QtWidgets.QFileDialog.ShowDirsOnly
            | QtWidgets.QFileDialog.DontResolveSymlinks,
        )

    def maskOpacityChanged(self):
        self.sldOpacity.textLab.setText(str(self.opacity))
        self._update_image()

    def clickRadiusChanged(self):
        self.sldClickRadius.textLab.setText(str(self.click_radius))
        self._update_image()

    def threshChanged(self):
        self.sldThresh.textLab.setText(str(self.seg_thresh))
        self.controller.prob_thresh = self.seg_thresh
        self._update_image()

    def undoClick(self):
        if self.image is None:
            return
        self.controller.undo_click()

    def undoAll(self):
        self.controller.reset_last_object()

    def redoClick(self):
        print("重做功能还没有实现")

    def canvasClick(self, x, y, isLeft):
        if self.controller is None:
            return
        if self.controller.image is None:
            return
        if x < 0 or y < 0:
            return
        if not self.controller.curr_label_number:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("未选择当前标签")
            msg.setText("请先在标签列表中单击点选标签")
            msg.setStandardButtons(QMessageBox.Yes)
            res = msg.exec_()
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
        if reset_canvas:
            self.zoom_restart(width, height)
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

    # 界面缩放重置
    def zoom_restart(self, width, height):
        # 每次加载图像前设定下当前的显示框，解决图像缩小后不在中心的问题
        self.scene.setSceneRect(0, 0, width, height)
        # 缩放清除
        self.canvas.scale(1 / self.canvas.zoom_all, 1 / self.canvas.zoom_all)  # 重置缩放
        self.canvas.zoom_all = 1
        # 最佳缩放
        s_eps = 5e-2
        scr_cont = [
            self.scrollArea.width() / width - s_eps,
            self.scrollArea.height() / height - s_eps,
        ]
        if scr_cont[0] * height > self.scrollArea.height():
            self.canvas.zoom_all = scr_cont[1]
        else:
            self.canvas.zoom_all = scr_cont[0]
        self.canvas.scale(self.canvas.zoom_all, self.canvas.zoom_all)
