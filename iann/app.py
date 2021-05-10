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

from .controller import InteractiveController
from .ui import Ui_IANN, Ui_Help
from .models import models
import iann.util as util

__appname__ = "IANN"
here = osp.dirname(osp.abspath(__file__))


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
        self.labelPaths = []  # 保存所有从outputdir发现的标签文件路径
        self.currIdx = 0  # 标注文件夹时到第几个了
        self.currentPath = None
        self.filePaths = []  # 标注文件夹时所有文件路径
        # TODO: labelList用一个class实现
        self.labelList = []  # 标签列表(数字，名字，颜色)
        self.config = util.parseConfigs(osp.join(here, "config/config.yaml"))
        # self.labelList = [[1, "人", [0, 0, 0]], [2, "车", [128, 128, 128]]]
        self.isDirty = False
        self.settings = QtCore.QSettings("PaddleCV-SIG", "IANN")

        self.recentFiles = self.settings.value("recent_files", [])
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

        # 标签列表点击
        self.labelListTable.cellDoubleClicked.connect(self.labelListDoubleClick)
        self.labelListTable.cellClicked.connect(self.labelListClicked)
        self.labelListTable.cellChanged.connect(self.labelListItemChanged)

        labelListFile = self.settings.value("label_list_file")
        print(labelListFile)
        self.labelList = util.readLabel(labelListFile)
        self.refreshLabelList()

        # TODO: 打开上次关软件时用的模型
        # TODO: 在ui展示后再加载模型

    def updateFileMenu(self):
        def exists(filename):
            return osp.exists(str(filename))

        menu = self.actions.recent_files
        menu.clear()
        print("recentFiles", self.recentFiles)
        files = [f for f in self.recentFiles if f != self.currentPath and exists(f)]
        for i, f in enumerate(files):
            icon = util.newIcon("next")
            action = QtWidgets.QAction(
                icon, "&%d %s" % (i + 1, QtCore.QFileInfo(f).fileName()), self
            )
            action.triggered.connect(partial(self.loadImage, f))
            menu.addAction(action)

    def toBeImplemented(self):
        self.statusbar.showMessage("功能尚在开发")

    def initActions(self):
        def menu(title, actions=None):
            menu = self.menuBar().addMenu(title)
            if actions:
                util.addActions(menu, actions)
            return menu

        action = partial(util.newAction, self)
        shortcuts = self.config["shortcut"]
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
        open_recent = action(
            self.tr("&最近标注"),
            self.toBeImplemented,
            "",
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
            self.undoAll,
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
        save = action(
            self.tr("&保存"),
            self.saveLabel,
            "",
            "redo",
            self.tr("保存图像标签"),
        )
        save_as = action(
            self.tr("&另存为"),
            partial(self.saveLabel, True),
            "",
            "redo",
            self.tr("指定标签保存路径"),
        )
        auto_save = action(
            self.tr("&自动保存"),
            self.toggleAutoSave,
            "",
            None,
            self.tr("翻页同时自动保存"),
            checkable=True,
        )
        auto_save.setChecked(self.config.get("auto_save", False))

        recent = action(
            self.tr("&近期图片"),
            self.toBeImplemented,
            "",
            "redo",
            self.tr("近期打开的图片"),
        )
        close = action(
            self.tr("&关闭"),
            self.toBeImplemented,
            "",
            "redo",
            self.tr("关闭当前图像"),
        )
        connected = action(
            self.tr("&连通块"),
            self.toBeImplemented,
            "",
            "redo",
            self.tr(""),
        )
        quit = action(
            self.tr("&退出"),
            self.close,
            "",
            "redo",
            self.tr("退出软件"),
        )
        save_label = action(
            self.tr("&保存标签列表"),
            self.saveLabelList,
            "",
            "redo",
            self.tr("将标签保存成标签配置文件"),
        )
        load_label = action(
            self.tr("&加载标签列表"),
            self.loadLabelList,
            "",
            "redo",
            self.tr("从标签配置文件中加载标签"),
        )
        clear_label = action(
            self.tr("&清空标签列表"),
            self.clearLabelList,
            "",
            "redo",
            self.tr("清空所有的标签"),
        )
        shortcuts = action(
            self.tr("&快捷键列表"),
            self.showShortcuts,
            "",
            "redo",
            self.tr("查看所有快捷键"),
        )
        recent_files = QtWidgets.QMenu(self.tr("近期文件"))
        recent_files.aboutToShow.connect(self.updateFileMenu)
        # TODO: 改用manager
        self.actions = util.struct(
            auto_save=auto_save,
            recent_files=recent_files,
            fileMenu=(
                open_image,
                open_folder,
                change_output_dir,
                recent_files,
                None,
                save,
                save_as,
                auto_save,
                turn_next,
                turn_prev,
                close,
                None,
                quit,
            ),
            labelMenu=(save_label, load_label, clear_label, None, grid_ann),
            helpMenu=(quick_start, about, shortcuts),
            toolBar=(finish_object, clear, undo, redo, turn_prev, turn_next),
        )
        menu("文件", self.actions.fileMenu)
        menu("标注", self.actions.labelMenu)
        menu("帮助", self.actions.helpMenu)
        util.addActions(self.toolBar, self.actions.toolBar)

    def queueEvent(self, function):
        # TODO: 研究这个东西是不是真的不影响ui
        QtCore.QTimer.singleShot(0, function)

    def showShortcuts(self):
        pass

    def toggleAutoSave(self, save):
        if save and not self.outputDir:
            self.changeOutputDir()
        if save and not self.outputDir:
            save = False
        self.actions.auto_save.setChecked(save)
        self.config["auto_save"] = save
        util.saveConfigs(osp.join(here, "config/config.yaml"), self.config)

    def changeModel(self, idx):
        # TODO: 设置gpu还是cpu运行
        self.statusbar.showMessage(f"正在加载 {models[idx].name} 模型")
        model = models[idx].get_model()
        if self.controller is None:
            self.controller = InteractiveController(
                model,
                predictor_params={"brs_mode": "f-BRS-B"},
                update_image_callback=self._update_image,
            )
            self.controller.prob_thresh = self.segThresh
            # 这里如果直接加载模型会报错，先判断有没有图像
            if self.image is not None:
                self.controller.set_image(self.image)
        else:
            self.controller.reset_predictor(model)

        self.statusbar.showMessage(f"{ models[idx].name}模型加载完成", 5000)

    def loadLabelList(self):
        filters = self.tr("标签配置文件 (*.txt)")
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            self.tr("%s - 选择标签配置文件路径") % __appname__,
            ".",
            filters,
        )
        if file_path == "":  # 不加判断打开保存界面然后关闭会报错，主要是刷新列表
            return
        self.labelList = util.readLabel(file_path)
        print(self.labelList)
        self.refreshLabelList()
        self.settings.setValue("label_list_file", file_path)

    def saveLabelList(self):
        if len(self.labelList) == 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("没有需要保存的标签")
            msg.setText("请先添加标签之后再进行保存")
            msg.setStandardButtons(QMessageBox.Yes)
            res = msg.exec_()
        filters = self.tr("标签配置文件 (*.txt)")
        dlg = QtWidgets.QFileDialog(self, "保存标签配置文件", ".", filters)
        dlg.setDefaultSuffix("txt")
        dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        dlg.setOption(QtWidgets.QFileDialog.DontConfirmOverwrite, False)
        dlg.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, False)
        savePath, _ = dlg.getSaveFileName(
            self,
            self.tr("保存标签配置文件"),
            ".",
        )
        # print(savePath)
        self.settings.setValue("label_list_file", savePath)
        util.saveLabel(self.labelList, savePath)

    def addLabel(self):
        c = [255, 0, 0]  # TODO: 随机生成一个颜色
        table = self.labelListTable
        table.insertRow(table.rowCount())
        idx = table.rowCount() - 1
        self.labelList.append([idx + 1, "", c])

        numberItem = QTableWidgetItem(str(idx + 1))
        numberItem.setFlags(QtCore.Qt.ItemIsEnabled)
        table.setItem(idx, 0, numberItem)

        table.setItem(idx, 1, QTableWidgetItem())

        colorItem = QTableWidgetItem()
        colorItem.setBackground(QtGui.QColor(c[0], c[1], c[2]))
        colorItem.setFlags(QtCore.Qt.ItemIsEnabled)
        table.setItem(idx, 2, colorItem)

        delItem = QTableWidgetItem()
        delItem.setIcon(util.newIcon("clear"))
        delItem.setTextAlignment(Qt.AlignCenter)
        delItem.setFlags(QtCore.Qt.ItemIsEnabled)
        table.setItem(idx, 3, delItem)

    def clearLabelList(self):
        self.labelList = []
        if self.controller:
            self.controller.label_list = []
            self.controller.curr_label_number = None
        self.labelListTable.clear()
        self.labelListTable.setRowCount(0)

    def refreshLabelList(self):
        table = self.labelListTable
        table.clearContents()
        table.setRowCount(len(self.labelList))
        table.setColumnCount(4)
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
            delItem = QTableWidgetItem()
            delItem.setIcon(util.newIcon("clear"))
            delItem.setTextAlignment(Qt.AlignCenter)
            delItem.setFlags(QtCore.Qt.ItemIsEnabled)
            table.setItem(idx, 3, delItem)

        cols = [0, 1, 3]
        for idx in cols:
            table.resizeColumnToContents(idx)

    def labelListDoubleClick(self, row, col):
        print("cell double clicked", row, col)
        if col != 2:
            return
        table = self.labelListTable
        color = QtWidgets.QColorDialog.getColor()
        # BUG: 判断颜色没变
        print(color.getRgb())
        table.item(row, col).setBackground(color)
        self.labelList[row][2] = color.getRgb()[:3]
        if self.controller:
            self.controller.label_list = self.labelList

    def labelListClicked(self, row, col):
        print("cell clicked", row, col)
        table = self.labelListTable
        if col == 3:
            table.removeRow(row)
            del self.labelList[row]
        if col == 0 or col == 1:
            for idx in range(len(self.labelList)):
                table.item(idx, 0).setBackground(QtGui.QColor(255, 255, 255))
            table.item(row, 0).setBackground(QtGui.QColor(48, 140, 198))
            for idx in range(3):
                table.item(row, idx).setSelected(True)
            if self.controller:
                print(int(table.item(row, 0).text()))
                self.controller.change_label_num(int(table.item(row, 0).text()))
                self.controller.label_list = self.labelList

    def labelListItemChanged(self, row, col):
        print("cell changed", row, col)
        if col != 1:
            return
        name = self.labelListTable.item(row, col).text()
        self.labelList[row - 1][1] = name

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
        self.queueEvent(partial(self.loadImage, file_path))
        self.imagePath = file_path

    def loadLabel(self, imgPath):
        if imgPath == "" or len(self.labelPaths) == 0:
            return None

        def getName(path):
            return osp.basename(path).split(".")[0]

        imgName = getName(imgPath)
        for path in self.labelPaths:
            if getName(path) == imgName:
                labPath = path
                print(labPath)
                break
        label = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        print("label shape", label.shape)
        return label

    def loadImage(self, path):
        if len(path) == 0 or not osp.exists(path):
            return
        # TODO: 在不同平台测试含中文路径
        image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), 1)
        image = image[:, :, ::-1]  # BGR转RGB
        self.image = image
        self.currentPath = path
        if self.controller:
            self.controller.set_image(self.image)
        else:
            self.changeModel(0)
        self.controller.set_label(self.loadLabel(path))
        if path not in self.recentFiles:
            self.recentFiles.append(path)
            if len(self.recentFiles) > 10:
                del self.recentFiles[0]
            self.settings.setValue("recent_files", self.recentFiles)

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
        self.completeLastMask()
        if self.isDirty:
            if self.actions.auto_save.isChecked():
                self.saveLabel()
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("保存标签？")
                msg.setText("标签尚未保存，是否保存标签")
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
                res = msg.exec_()
                if res == QMessageBox.Yes:
                    self.saveLabel()

        imagePath = self.filePaths[self.currIdx]
        self.loadImage(imagePath)
        self.imagePath = imagePath
        self.listFiles.setCurrentRow(self.currIdx)
        self.setClean()

    def finishObject(self):
        if self.image is None:
            return
        if not self.controller:
            return
        self.controller.finish_object()
        self.setDirty()

    def completeLastMask(self):
        # 返回最后一个标签是否完成，false就是还有带点的
        if not self.controller:
            return True
        if not self.controller.is_incomplete_mask:
            return True
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("完成最后一个目标？")
        msg.setText("是否完成最后一个目标的标注，不完成不会进行保存。")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        res = msg.exec_()
        if res == QMessageBox.Yes:
            self.finishObject()
            self.setDirty()
            return True
        return False

    def saveLabel(self, saveAs=False, savePath=None):
        if not self.controller:
            return
        if self.controller.image is None:
            return
        self.completeLastMask()
        if not savePath:  # 参数没传存到哪
            if not saveAs and self.outputDir is not None:
                # 指定了标签文件夹，而且不是另存为
                savePath = osp.join(
                    self.outputDir, osp.basename(self.imagePath).split(".")[0] + ".png"
                )
            else:
                filters = self.tr("Label files (*.png)")
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

        cv2.imwrite(savePath, self.controller.result_mask)
        self.setClean()
        self.statusbar.showMessage(f"标签成功保存至 {savePath}")

    def setClean(self):
        self.isDirty = False

    def setDirty(self):
        self.isDirty = True

    def changeOutputDir(self):
        outputDir = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            self.tr("%s - 选择标签保存路径") % __appname__,
            # osp.dirname(self.imagePath),
            ".",
            QtWidgets.QFileDialog.ShowDirsOnly
            | QtWidgets.QFileDialog.DontResolveSymlinks,
        )
        if len(outputDir) == 0 or not osp.exists(outputDir):
            return False
        labelPaths = os.listdir(outputDir)
        exts = ["png"]
        labelPaths = [n for n in labelPaths if n.split(".")[-1] in exts]
        labelPaths = [osp.join(outputDir, n) for n in labelPaths]
        self.outputDir = outputDir
        self.labelPaths = labelPaths
        return True

    def maskOpacityChanged(self):
        self.sldOpacity.textLab.setText(str(self.opacity))
        self._update_image()

    def clickRadiusChanged(self):
        self.sldClickRadius.textLab.setText(str(self.clickRadius))
        self._update_image()

    def threshChanged(self):
        self.sldThresh.textLab.setText(str(self.segThresh))
        if self.controller:
            self.controller.prob_thresh = self.segThresh
        self._update_image()

    def undoClick(self):
        if self.image is None:
            return
        if not self.controller:
            return
        self.controller.undo_click()
        if not self.controller.is_incomplete_mask:
            self.setClean()

    def undoAll(self):
        if not self.controller:
            return
        self.controller.reset_last_object()
        self.setClean()

    def redoClick(self):
        self.toBeImplemented()

    def canvasClick(self, x, y, isLeft):
        if self.controller is None:
            return
        if self.controller.image is None:
            return
        currLabel = self.controller.curr_label_number
        if not currLabel or currLabel == 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("未选择当前标签")
            msg.setText("请先在标签列表中单击点选标签")
            msg.setStandardButtons(QMessageBox.Yes)
            res = msg.exec_()
            return

        self.controller.add_click(x, y, isLeft)

    def _update_image(self, reset_canvas=False):
        if not self.controller:
            return
        image = self.controller.get_visualization(
            alpha_blend=self.opacity,
            click_radius=self.clickRadius,
        )
        height, width, channel = image.shape
        bytesPerLine = 3 * width
        image = QImage(image.data, width, height, bytesPerLine, QImage.Format_RGB888)
        if reset_canvas:
            self.resetZoom(width, height)
        self.scene.addPixmap(QPixmap(image))
        # TODO: 研究是否有类似swap的更高效方式
        self.scene.removeItem(self.scene.items()[1])

    # 界面缩放重置
    def resetZoom(self, width, height):
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

    @property
    def opacity(self):
        return self.sldOpacity.value() / 10

    @property
    def clickRadius(self):
        return self.sldClickRadius.value()

    @property
    def segThresh(self):
        return self.sldThresh.value() / 10
