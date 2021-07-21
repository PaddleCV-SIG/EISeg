from genericpath import exists
import os
import os.path as osp
from functools import partial
import sys
import inspect
import warnings
import json
import collections
from distutils.util import strtobool
import imghdr

from qtpy import QtGui, QtCore, QtWidgets
from qtpy.QtWidgets import QMainWindow, QMessageBox, QTableWidgetItem
from qtpy.QtGui import QImage, QPixmap, QPolygonF, QPen
from qtpy.QtCore import Qt, QFile, QByteArray, QDataStream
import paddle
import cv2
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

from widget import ShortcutWindow
import models
from controller import InteractiveController
from ui import Ui_EISeg
from widget import PolygonAnnotation
from eiseg import pjpath, __APPNAME__
import util
from util.colormap import ColorMask
from util.label import LabeleList
from util import MODELS
from util.remotesensing import *
from util.language import TransUI


# DEBUG:
np.set_printoptions(threshold=sys.maxsize)
warnings.filterwarnings("ignore")


class APP_EISeg(QMainWindow, Ui_EISeg):
    IDILE, ANNING, EDITING = 0, 1, 2
    # IDILE：打开软件到模型和权重加载之前
    # ANNING：有未完成的交互式标注
    # EDITING：交互式标注完成，修改多边形

    def __init__(self, parent=None):
        super(APP_EISeg, self).__init__(parent)

        # 多语言
        self.settings = QtCore.QSettings(
            osp.join(pjpath, "config/setting.ini"), QtCore.QSettings.IniFormat
        )
        # self.settings.value("language_state", "False")
        is_trans = strtobool(self.settings.value("language_state", "False"))
        self.trans = TransUI(is_trans)

        # 初始化界面
        self.setupUi(self, self.trans)

        # app变量
        self.status = self.IDILE
        self.save_status = [False, True]  # 默认不保存伪彩色，保存JSON
        self.controller = None
        self.image = None  # 可能先加载图片后加载模型，只用于暂存图片
        self.modelClass = MODELS[0]
        self.outputDir = None  # 标签保存路径
        self.labelPaths = []  # 保存所有从outputdir发现的标签文件路径
        self.filePaths = []  # 文件夹下所有待标注图片路径
        self.currIdx = 0  # 文件夹标注当前图片下标
        self.currentPath = None
        self.isDirty = False
        self.labelList = LabeleList()
        self.rsRGB = [0, 0, 0]
        self.rawimg = None
        self.origExt = False
        # worker
        self.workers_show = [True, True, True, True, False, False]
        self.workers = [
            self.ModelDock,
            self.DataDock,
            self.LabelDock,
            self.ShowSetDock,
            self.RSDock,
            self.MIDock,
        ]
        self.config = util.parse_configs(osp.join(pjpath, "config/config.yaml"))
        self.recentModels = self.settings.value("recent_models", [])
        self.recentFiles = self.settings.value("recent_files", [])
        self.workerStatus = self.settings.value("worker_status", [])
        self.layoutStatus = self.settings.value("layout_status", QByteArray())
        self.languageState = self.settings.value("language_state", bool)
        if not self.recentFiles:
            self.recentFiles = []
        self.maskColormap = ColorMask(osp.join(pjpath, "config/colormap.txt"))

        # 初始化action
        self.initActions()

        # 更新近期记录
        self.refreshWorker(True)
        self.updateModelsMenu()
        self.updateRecentFile()
        self.loadLayout()

        # 窗口
        ## 快捷键
        self.shortcutWindow = ShortcutWindow(self.actions, pjpath)

        ## 画布部分
        self.scene.clickRequest.connect(self.canvasClick)
        self.canvas.zoomRequest.connect(self.viewZoomed)
        self.annImage = QtWidgets.QGraphicsPixmapItem()
        self.scene.addItem(self.annImage)

        ## 按钮点击
        self.btnSave.clicked.connect(self.saveLabel)  # 保存
        self.listFiles.itemDoubleClicked.connect(self.listClicked)  # 标签列表点击
        self.comboModelSelect.currentIndexChanged.connect(self.changeModel)  # 模型选择
        self.btnAddClass.clicked.connect(self.addLabel)
        self.btnParamsSelect.clicked.connect(self.changeParam)  # 模型参数选择

        ## 滑动
        self.sldOpacity.valueChanged.connect(self.maskOpacityChanged)
        self.sldClickRadius.valueChanged.connect(self.clickRadiusChanged)
        self.sldThresh.valueChanged.connect(self.threshChanged)

        ## 标签列表点击
        self.labelListTable.cellDoubleClicked.connect(self.labelListDoubleClick)
        self.labelListTable.cellClicked.connect(self.labelListClicked)
        self.labelListTable.cellChanged.connect(self.labelListItemChanged)
        # self.refreshLabelList()
        label_list_file = self.settings.value("label_list_file", None)
        if label_list_file is not None:
            self.loadLabelList(self.settings.value("label_list_file"))

        ## 功能区选择
        # self.rsShow.currentIndexChanged.connect(self.rsShowModeChange)  # 显示模型
        for bandCombo in self.bandCombos:
            bandCombo.currentIndexChanged.connect(self.rsBandSet)  # 设置波段

    def editShortcut(self):
        self.shortcutWindow.show()

    def initActions(self):
        def menu(title, actions=None):
            menu = self.menuBar().addMenu(title)
            if actions:
                util.addActions(menu, actions)
            return menu

        tr = self.tr
        action = partial(util.newAction, self)
        # shortcuts = self.config["shortcut"]
        self.actions = util.struct()
        start = dir()
        edit_shortcuts = action(
            tr("&编辑快捷键"),
            self.editShortcut,
            "edit_shortcuts",
            "Shortcut",
            self.trans.put("编辑软件快捷键"),
        )
        turn_prev = action(
            "&" + self.trans.put("上一张"),
            partial(self.turnImg, -1),
            "turn_prev",
            "Prev",
            self.trans.put("翻到上一张图片"),
        )
        turn_next = action(
            "&" + self.trans.put("下一张"),
            partial(self.turnImg, 1),
            "turn_next",
            "Next",
            self.trans.put("翻到下一张图片"),
        )
        open_image = action(
            "&" + self.trans.put("打开图像"),
            self.openImage,
            "open_image",
            "OpenImage",
            self.trans.put("打开一张图像进行标注"),
        )
        open_folder = action(
            "&" + self.trans.put("打开文件夹"),
            self.openFolder,
            "open_folder",
            "OpenFolder",
            self.trans.put("打开一个文件夹下所有的图像进行标注"),
        )
        change_output_dir = action(
            "&" + self.trans.put("改变标签保存路径"),
            partial(self.changeOutputDir, None),
            "change_output_dir",
            "ChangeLabelPath",
            self.trans.put("改变标签保存的文件夹路径"),
        )
        load_param = action(
            "&" + self.trans.put("加载模型参数"),
            self.changeParam,
            "load_param",
            "Model",
            self.trans.put("加载一个模型参数"),
        )
        quick_start = action(
            "&" + self.trans.put("快速上手"),
            self.toBeImplemented,
            "quick_start",
            "Use",
            self.trans.put("快速上手介绍"),
        )
        about = action(
            "&" + self.trans.put("关于软件"),
            self.toBeImplemented,
            "about",
            "About",
            self.trans.put("关于这个软件和开发团队"),
        )
        grid_ann = action(
            "&" + self.trans.put("N2宫格标注"),
            self.toBeImplemented,
            "grid_ann",
            "N2",
            self.trans.put("使用N2宫格进行细粒度标注"),
        )
        finish_object = action(
            "&" + self.trans.put("完成当前目标"),
            self.finishObject,
            "finish_object",
            "Ok",
            self.trans.put("完成当前目标的标注"),
        )
        clear = action(
            "&" + self.trans.put("清除所有标注"),
            self.undoAll,
            "clear",
            "Clear",
            self.trans.put("清除所有标注信息"),
        )
        undo = action(
            "&" + self.trans.put("撤销"),
            self.undoClick,
            "undo",
            "Undo",
            self.trans.put("撤销一次点击"),
        )
        redo = action(
            "&" + self.trans.put("重做"),
            self.redoClick,
            "redo",
            "Redo",
            self.trans.put("重做一次点击"),
        )
        save = action(
            "&" + self.trans.put("保存"),
            self.saveLabel,
            "save",
            "Save",
            self.trans.put("保存图像标签"),
        )
        save_as = action(
            "&" + self.trans.put("另存为"),
            partial(self.saveLabel, True),
            "save_as",
            "OtherSave",
            self.trans.put("指定标签保存路径"),
        )
        auto_save = action(
            "&" + self.trans.put("自动保存"),
            self.toggleAutoSave,
            "auto_save",
            "AutoSave",
            self.trans.put("翻页同时自动保存"),
            checkable=True,
        )
        # auto_save.setChecked(self.config.get("auto_save", False))
        del_active_point = action(
            "&" + self.trans.put("删除点"),
            self.delActivePoint,
            "del_active_point",
            "RemovePolygonPoint",
            self.trans.put("删除当前选中的点"),
        )
        del_active_polygon = action(
            "&" + self.trans.put("删除多边形"),
            self.delActivePolygon,
            "del_active_polygon",
            "RemovePolygon",
            self.trans.put("删除当前选中的多边形"),
        )
        largest_component = action(
            "&" + self.trans.put("保留最大连通块"),
            self.toggleLargestCC,
            "largest_component",
            "SaveMaxPolygon",
            self.trans.put("保留最大的连通块"),
            checkable=True,
        )
        save_color = action(
            "&" + self.trans.put("伪彩色保存"),
            partial(self.changeSave, 0),
            "save_color",
            "SavePseudoColor",
            self.trans.put("保存为伪彩色图像"),
            checkable=True,
        )
        save_json = action(
            "&" + self.trans.put("JSON保存"),
            partial(self.changeSave, 1),
            "save_json",
            "SaveJson",
            self.trans.put("保存为JSON格式"),
            checkable=True,
            checked=True,
        )
        close = action(
            "&" + self.trans.put("关闭"),
            self.toBeImplemented,
            "close",
            "End",
            self.trans.put("关闭当前图像"),
        )
        quit = action(
            "&" + self.trans.put("退出"),
            self.close,
            "quit",
            "Close",
            self.trans.put("退出软件"),
        )
        save_label = action(
            "&" + self.trans.put("保存标签列表"),
            partial(self.saveLabelList, None),
            "save_label",
            "ExportLabel",
            self.trans.put("将标签保存成标签配置文件"),
        )
        load_label = action(
            "&" + self.trans.put("加载标签列表"),
            partial(self.loadLabelList, None),
            "load_label",
            "ImportLabel",
            self.trans.put("从标签配置文件中加载标签"),
        )
        clear_label = action(
            "&" + self.trans.put("清空标签列表"),
            self.clearLabelList,
            "clear_label",
            "ClearLabel",
            self.trans.put("清空所有的标签"),
        )
        clear_recent = action(
            "&" + self.trans.put("清除标注记录"),
            self.clearRecentFile,
            "clear_recent",
            "ClearRecent",
            self.trans.put("清除近期标注记录"),
        )
        model_worker = action(
            "&" + self.trans.put("模型区"),
            partial(self.changeWorkerShow, 0),
            "model_worker",
            "Net",
            self.trans.put("模型区"),
            checkable=True,
        )
        data_worker = action(
            "&" + self.trans.put("数据区"),
            partial(self.changeWorkerShow, 1),
            "data_worker",
            "Data",
            self.trans.put("数据区"),
            checkable=True,
        )
        label_worker = action(
            "&" + self.trans.put("标签区"),
            partial(self.changeWorkerShow, 2),
            "label_worker",
            "Label",
            self.trans.put("标签区"),
            checkable=True,
        )
        set_worker = action(
            "&" + self.trans.put("设置区"),
            partial(self.changeWorkerShow, 3),
            "set_worker",
            "Setting",
            self.trans.put("设置区"),
            checkable=True,
        )
        rs_worker = action(
            "&" + self.trans.put("遥感区"),
            partial(self.changeWorkerShow, 4),
            "remote_worker",
            "RemoteSensing",
            self.trans.put("遥感区"),
            checkable=True,
        )
        mi_worker = action(
            "&" + self.trans.put("医疗区"),
            partial(self.changeWorkerShow, 5),
            "medical_worker",
            "MedicalImaging",
            self.trans.put("医疗区"),
            checkable=True,
        )
        language = action(
            "&" + self.trans.put("中国中文"),
            self.setLanguage,
            "language",
            "Language",
            self.trans.put("切换语言，重启生效"),
            checkable=True,
            checked=bool(strtobool(self.settings.value("language_state")) - 1),
        )
        for name in dir():
            if name not in start:
                self.actions.append(eval(name))
        recent_files = QtWidgets.QMenu(self.trans.put("近期文件"))
        recent_files.aboutToShow.connect(self.updateRecentFile)
        recent_params = QtWidgets.QMenu(self.trans.put("近期模型及参数"))
        recent_params.aboutToShow.connect(self.updateModelsMenu)

        self.menus = util.struct(
            recent_files=recent_files,
            recent_params=recent_params,
            fileMenu=(
                open_image,
                open_folder,
                change_output_dir,
                load_param,
                clear_recent,
                recent_files,
                recent_params,
                None,
                save,
                save_as,
                auto_save,
                None,
                turn_next,
                turn_prev,
                close,
                None,
                quit,
            ),
            labelMenu=(
                save_label,
                load_label,
                clear_label,
                None,
                grid_ann,
                None,
                largest_component,
                del_active_polygon,
                del_active_point,
            ),
            workMenu=(save_color, save_json),
            showMenu=(
                model_worker,
                data_worker,
                label_worker,
                set_worker,
                rs_worker,
                mi_worker,
            ),
            helpMenu=(language, quick_start, about, edit_shortcuts),
            toolBar=(
                finish_object,
                clear,
                undo,
                redo,
                turn_prev,
                turn_next,
                None,
                save_color,
                save_json,
                None,
                largest_component,
            ),
        )
        menu(self.trans.put("文件"), self.menus.fileMenu)
        menu(self.trans.put("标注"), self.menus.labelMenu)
        menu(self.trans.put("功能"), self.menus.workMenu)
        menu(self.trans.put("显示"), self.menus.showMenu)
        menu(self.trans.put("帮助"), self.menus.helpMenu)
        util.addActions(self.toolBar, self.menus.toolBar)

    def updateRecentFile(self):
        menu = self.menus.recent_files
        menu.clear()
        recentFiles = self.settings.value("recent_files", [])
        if not recentFiles:
            recentFiles = []
        files = [f for f in recentFiles if osp.exists(f)]
        for i, f in enumerate(files):
            icon = util.newIcon("File")
            action = QtWidgets.QAction(
                icon, "&【%d】 %s" % (i + 1, QtCore.QFileInfo(f).fileName()), self
            )
            action.triggered.connect(partial(self.loadImage, f, True))
            menu.addAction(action)
        if len(files) == 0:
            menu.addAction(self.trans.put("无近期文件"))
        self.settings.setValue("recent_files", files)

    def addRecentFile(self, path):
        if not osp.exists(path):
            return
        paths = self.settings.value("recent_files")
        if not paths:
            paths = []
        if path not in paths:
            paths.append(path)
        if len(paths) > 15:
            del paths[0]
        self.settings.setValue("recent_files", paths)
        self.updateRecentFile()

    def clearRecentFile(self):
        self.settings.remove("recent_files")
        self.statusbar.showMessage(self.trans.put("已清除最近打开文件"), 10000)

    def updateModelsMenu(self):
        menu = self.menus.recent_params
        menu.clear()
        self.recentModels = [
            m for m in self.recentModels if osp.exists(m["param_path"])
        ]
        for idx, m in enumerate(self.recentModels):
            icon = util.newIcon("Model")
            action = QtWidgets.QAction(
                icon,
                f"&【{m['model_name']}】 {osp.basename(m['param_path'])}",
                self,
            )
            action.triggered.connect(
                partial(self.loadModelParam, m["param_path"], m["model_name"])
            )
            menu.addAction(action)
        self.settings.setValue("recent_params", self.recentModels)

    def changeModel(self, idx):
        self.modelClass = MODELS[idx]

    def changeParam(self):
        if not self.modelClass:
            self.warn(
                self.trans.put("选择模型结构"), self.trans.put("尚未选择模型结构，请在右侧下拉菜单进行选择！")
            )
        formats = ["*.pdparams"]
        filters = "paddle model param files (%s)" % " ".join(formats)
        start_path = (
            "."
            if len(self.recentModels) == 0
            else osp.dirname(self.recentModels[-1]["param_path"])
        )
        param_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            self.trans.put("选择模型参数") + " - " + __APPNAME__,
            start_path,
            filters,
        )
        if not osp.exists(param_path):
            return
        res = self.loadModelParam(param_path)
        if res:
            model_dict = {
                "param_path": param_path,
                "model_name": self.modelClass.__name__,
            }
            if model_dict not in self.recentModels:
                self.recentModels.append(model_dict)
                if len(self.recentModels) > 10:
                    del self.recentModels[0]
                self.settings.setValue("recent_models", self.recentModels)

    def loadModelParam(self, param_path, model=None):
        print("Call load model param: ", param_path, model, type(model))
        # TODO: 捕获加载模型过程中所有的错误，
        # TODO: 对paddle版本不到2.1.0进行提示
        if model is None:
            model = self.modelClass()
        if isinstance(model, str):
            try:
                model = MODELS[model]()
            except KeyError:
                print("Model don't exist")
                return False
        if inspect.isclass(model):
            model = model()
        if not isinstance(model, models.EISegModel):
            print("not a instance")
            self.warn(
                self.trans.put("选择模型结构"), self.trans.put("尚未选择模型结构，请在右侧下拉菜单进行选择！")
            )
            return False
        modelIdx = MODELS.idx(model.__name__)
        self.statusbar.showMessage(
            self.trans.put("正在加载") + " " + model.__name__
        )  # 这里没显示
        model = model.load_param(param_path)
        if model is not None:
            if self.controller is None:
                self.controller = InteractiveController(
                    model,
                    predictor_params={
                        # 'brs_mode': 'f-BRS-B',
                        "brs_mode": "NoBRS",
                        "prob_thresh": 0.5,
                        "zoom_in_params": {
                            "skip_clicks": -1,
                            "target_size": (400, 400),
                            "expansion_ratio": 1.4,
                        },
                        "predictor_params": {"net_clicks_limit": None, "max_size": 800},
                        "brs_opt_func_params": {"min_iou_diff": 0.001},
                        "lbfgs_params": {"maxfun": 20},
                    },
                    update_image_callback=self._update_image,
                )
                self.controller.prob_thresh = self.segThresh
                if self.image is not None:
                    self.controller.set_image(self.image)
            else:
                self.controller.reset_predictor(model)
            self.statusbar.showMessage(
                osp.basename(param_path) + " " + self.trans.put("模型加载完成"), 20000
            )
            self.comboModelSelect.setCurrentIndex(modelIdx)
            return True
        else:  # 模型和参数不匹配
            self.warn(
                self.trans.put("模型和参数不匹配"),
                self.trans.put("当前网络结构中的参数与模型参数不匹配，请更换网络结构或使用其他参数！"),
            )
            self.statusbar.showMessage(self.trans.put("模型和参数不匹配，请重新加载"), 20000)
            self.controller = None  # 清空controller
            return False

    def loadRecentModelParam(self):
        if len(self.recentModels) == 0:
            self.statusbar.showMessage(self.trans.put("没有最近使用模型信息，请加载模型"), 10000)
            return
        m = self.recentModels[-1]
        model = MODELS[m["model_name"]]
        param_path = m["param_path"]
        self.loadModelParam(param_path, model)

    def loadLabelList(self, file_path=None):
        if file_path is None:
            filters = self.trans.put("标签配置文件") + " (*.txt)"
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                self.trans.put("选择标签配置文件路径") + " - " + __APPNAME__,
                ".",
                filters,
            )
        if not osp.exists(file_path):
            return
        self.labelList.readLabel(file_path)
        self.maskColormap.index = len(self.labelList)  # 颜色表跟上
        print("Loaded label list:", self.labelList.list)
        self.refreshLabelList()
        self.settings.setValue("label_list_file", file_path)

    def saveLabelList(self, auto_save_path=None):
        if len(self.labelList) == 0:
            self.warn(self.trans.put("没有需要保存的标签"), self.trans.put("请先添加标签之后再进行保存！"))
            return
        if auto_save_path is None:
            filters = self.trans.put("标签配置文件") + "(*.txt)"
            dlg = QtWidgets.QFileDialog(self, self.trans.put("保存标签配置文件"), ".", filters)
            dlg.setDefaultSuffix("txt")
            dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
            dlg.setOption(QtWidgets.QFileDialog.DontConfirmOverwrite, False)
            dlg.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, False)
            savePath, _ = dlg.getSaveFileName(
                self, self.trans.put("选择保存标签配置文件路径") + " - " + __APPNAME__, ".", filters
            )
        else:
            savePath = auto_save_path
        self.labelList.saveLabel(savePath)
        print("Save label list:", self.labelList.list, savePath)
        if auto_save_path is None:
            self.settings.setValue("label_list_file", savePath)

    def addLabel(self):
        c = self.maskColormap.get_color()
        table = self.labelListTable
        idx = table.rowCount()
        table.insertRow(table.rowCount())
        self.labelList.add(idx + 1, "", c)
        print("append", self.labelList)
        numberItem = QTableWidgetItem(str(idx + 1))
        numberItem.setFlags(QtCore.Qt.ItemIsEnabled)
        table.setItem(idx, 0, numberItem)
        table.setItem(idx, 1, QTableWidgetItem())
        colorItem = QTableWidgetItem()
        colorItem.setBackground(QtGui.QColor(c[0], c[1], c[2]))
        colorItem.setFlags(QtCore.Qt.ItemIsEnabled)
        table.setItem(idx, 2, colorItem)
        delItem = QTableWidgetItem()
        delItem.setIcon(util.newIcon("Clear"))
        delItem.setTextAlignment(Qt.AlignCenter)
        delItem.setFlags(QtCore.Qt.ItemIsEnabled)
        table.setItem(idx, 3, delItem)
        self.adjustTableSize()

    def adjustTableSize(self):
        self.labelListTable.horizontalHeader().setDefaultSectionSize(25)
        self.labelListTable.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.Fixed
        )
        self.labelListTable.horizontalHeader().setSectionResizeMode(
            3, QtWidgets.QHeaderView.Fixed
        )
        self.labelListTable.horizontalHeader().setSectionResizeMode(
            2, QtWidgets.QHeaderView.Fixed
        )
        self.labelListTable.setColumnWidth(2, 50)
        print("end")

    def clearLabelList(self):
        self.labelList.clear()
        if self.controller:
            self.controller.label_list = []
            self.controller.curr_label_number = 0
        self.labelListTable.clear()
        self.labelListTable.setRowCount(0)

    def refreshLabelList(self):
        table = self.labelListTable
        table.clearContents()
        table.setRowCount(len(self.labelList))
        table.setColumnCount(4)
        for idx, lab in enumerate(self.labelList):
            numberItem = QTableWidgetItem(str(lab.idx))
            numberItem.setFlags(QtCore.Qt.ItemIsEnabled)
            table.setItem(idx, 0, numberItem)
            table.setItem(idx, 1, QTableWidgetItem(lab.name))
            c = lab.color
            colorItem = QTableWidgetItem()
            colorItem.setBackground(QtGui.QColor(c[0], c[1], c[2]))
            colorItem.setFlags(QtCore.Qt.ItemIsEnabled)
            table.setItem(idx, 2, colorItem)
            delItem = QTableWidgetItem()
            delItem.setIcon(util.newIcon("Clear"))
            delItem.setTextAlignment(Qt.AlignCenter)
            delItem.setFlags(QtCore.Qt.ItemIsEnabled)
            table.setItem(idx, 3, delItem)
            self.adjustTableSize()

        cols = [0, 1, 3]
        for idx in cols:
            table.resizeColumnToContents(idx)
        self.adjustTableSize()

    def labelListDoubleClick(self, row, col):
        print("Label list double clicked", row, col)
        if col != 2:
            return
        table = self.labelListTable
        color = QtWidgets.QColorDialog.getColor()
        if color.getRgb() == (0, 0, 0, 255):
            return
        print("Change to new color:", color.getRgb())
        table.item(row, col).setBackground(color)
        self.labelList[row].color = color.getRgb()[:3]
        if self.controller:
            self.controller.label_list = self.labelList
        for p in self.scene.polygon_items:
            p.setColor(self.labelList[p.labelIndex].color)

    @property
    def currLabelIdx(self):
        return self.controller.curr_label_number - 1

    def labelListClicked(self, row, col):
        print("cell clicked", row, col)
        table = self.labelListTable
        if col == 3:
            table.removeRow(row)
            self.labelList.remove(row)
        if col == 0 or col == 1:
            for idx in range(len(self.labelList)):
                table.item(idx, 0).setBackground(QtGui.QColor(255, 255, 255))
            table.item(row, 0).setBackground(QtGui.QColor(48, 140, 198))
            for idx in range(3):
                table.item(row, idx).setSelected(True)
            if self.controller:
                self.controller.change_label_num(int(table.item(row, 0).text()))
                self.controller.label_list = self.labelList

    def labelListItemChanged(self, row, col):
        if col != 1:
            return
        name = self.labelListTable.item(row, col).text()
        self.labelList[row].name = name

    def delActivePolygon(self):
        for idx, polygon in enumerate(self.scene.polygon_items):
            if polygon.hasFocus():
                res = self.warn(
                    self.trans.put("确认删除？"),
                    self.trans.put("确认要删除当前选中多边形标注？"),
                    QMessageBox.Yes | QMessageBox.Cancel,
                )
                if res == QMessageBox.Yes:
                    polygon.remove()

    def delActivePoint(self):
        for polygon in self.scene.polygon_items:
            polygon.removeFocusPoint()

    # 图片/标签 io
    def openImage(self):
        formats = [
            "*.{}".format(fmt.data().decode())
            for fmt in QtGui.QImageReader.supportedImageFormats()
        ]
        recentPath = self.settings.value("recent_files", [])
        if len(recentPath) == 0:
            recentPath = "."
        else:
            recentPath = osp.dirname(recentPath[-1])
        filters = "Image & Label files (%s)" % " ".join(formats)
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            self.trans.put("选择待标注图片") + " - " + __APPNAME__,
            recentPath,
            filters,
        )
        if len(file_path) == 0:
            return
        self.queueEvent(partial(self.loadImage, file_path))
        self.listFiles.addItems([file_path.replace("\\", "/")])
        self.filePaths.append(file_path)

    def openFolder(self):
        self.inputDir = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            self.trans.put("选择待标注图片文件夹") + " - " + __APPNAME__,
            "/home/lin/Desktop",
            QtWidgets.QFileDialog.ShowDirsOnly
            | QtWidgets.QFileDialog.DontResolveSymlinks,
        )
        if len(self.inputDir) == 0:
            return
        filePaths = os.listdir(self.inputDir)
        # 不设置默认保存到当前文件夹下
        opd = osp.join(self.inputDir, "label")
        self.outputDir = opd
        exts = QtGui.QImageReader.supportedImageFormats()
        filePaths = [n for n in filePaths if n.split(".")[-1] in exts]
        filePaths = [osp.join(self.inputDir, n) for n in filePaths]
        for p in filePaths:
            if p not in self.filePaths:
                self.filePaths.append(p)
                self.listFiles.addItem(p.replace("\\", "/"))
        # self.listFiles.addItems(filePaths)
        # 有已经标注的就加载
        if osp.exists(self.outputDir):
            self.changeOutputDir(self.outputDir)
        self.currIdx = 0
        self.turnImg(0)

    def loadImage(self, path, update_list=False):
        if len(path) == 0 or not osp.exists(path):
            return
        if imghdr.what(path) == "tiff":
            if self.RSDock.isVisible():
                self.rawimg, geoinfo = open_tif(path)
                try:
                    image = selec_band(self.rawimg, self.rsRGB)
                except IndexError:
                    self.rsRGB = [0, 0, 0]
                    image = selec_band(self.rawimg, self.rsRGB)
                self.update_bandList()
            else:
                self.warn(
                    self.trans.put("未打开遥感工具"),
                    self.trans.put("未打开遥感工具，请先在菜单栏-显示中打开遥感区！"),
                )
                return
        else:
            image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), 1)
            image = image[:, :, ::-1]  # BGR转RGB
        self.image = image
        self.currentPath = path
        if self.controller:
            self.controller.set_image(
                image
                # twoPercentLinear(image) if (self.RSDock.isVisible() and \
                # self.rsShow.currentIndex() == 1) else image
            )
        else:
            self.warn(self.trans.put("未加载模型"), self.trans.put("未加载模型参数，请先加载模型参数！"))
            self.changeParam()
            print("please load model params first!")
            return 0
        self.controller.set_label(self.loadLabel(path))
        self.addRecentFile(path)
        self.imagePath = path  # 修复使用近期文件的图像保存label报错
        if update_list:
            self.listFiles.addItems([path.replace("\\", "/")])
            self.filePaths.append(path)

    def loadLabel(self, imgPath):
        print("load label", imgPath, self.labelPaths)
        if imgPath == "" or len(self.labelPaths) == 0:
            return None

        def getName(path):
            return osp.basename(path).split(".")[0]

        imgName = getName(imgPath)
        labelPath = None
        for path in self.labelPaths:
            if getName(path) == imgName:
                labelPath = path
                break
        if not labelPath:
            return
        print("label path", labelPath)

        labelPath = labelPath[: -len("png")] + "json"
        labels = json.loads(open(labelPath, "r").read())
        print(labels)

        for label in labels:
            color = label["color"]
            labelIdx = label["labelIdx"]
            points = label["points"]
            poly = PolygonAnnotation(
                labelIdx, color, color, self.opacity
            )  # , self.scene)
            self.scene.addItem(poly)
            self.scene.polygon_items.append(poly)
            for p in points:
                poly.addPointLast(QtCore.QPointF(p[0], p[1]))

    def turnImg(self, delta):
        self.currIdx += delta
        if self.currIdx >= len(self.filePaths) or self.currIdx < 0:
            self.currIdx -= delta
            self.statusbar.showMessage(
                self.trans.put(f"没有{'后一张'if delta==1 else '前一张'}图片")
            )
            return
        self.completeLastMask()
        if self.isDirty:
            if self.actions.auto_save.isChecked():
                self.saveLabel()
            else:
                res = self.warn(
                    self.trans.put("保存标签？"),
                    self.trans.put("标签尚未保存，是否保存标签"),
                    QMessageBox.Yes | QMessageBox.Cancel,
                )
                if res == QMessageBox.Yes:
                    self.saveLabel()

        imagePath = self.filePaths[self.currIdx]
        # print("polygon_items1:", self.scene.polygon_items)
        # 倒序删除可以完全删除
        for p in self.scene.polygon_items[::-1]:
            p.remove()
        # print("polygon_items2:", self.scene.polygon_items)
        self.scene.polygon_items = []

        self.loadImage(imagePath)
        self.imagePath = imagePath
        self.listFiles.setCurrentRow(self.currIdx)
        self.setClean()

    def listClicked(self):
        if not self.controller:
            self.warn(self.trans.put("模型未加载"), self.trans.put("尚未加载模型，请先加载模型！"))
            self.changeParam()
            if not self.controller:
                return
        if self.controller.is_incomplete_mask:
            self.saveLabel()
        toRow = self.listFiles.currentRow()
        delta = toRow - self.currIdx
        self.turnImg(delta)

    def finishObject(self):
        if not self.controller or self.image is None:
            return
        current_mask = self.controller.finish_object()
        if current_mask is not None:
            current_mask = current_mask.astype(np.uint8) * 255
            polygons = util.get_polygon(current_mask)
            self.setDirty()
            color = self.labelList[self.currLabelIdx].color
            for points in polygons:
                if len(points) < 3:
                    continue
                poly = PolygonAnnotation(self.currLabelIdx, color, color, self.opacity)
                # TODO：编号问题在这里
                # 每次完成编辑后多边形的编号都变了
                poly.labelIndex = self.currLabelIdx
                self.scene.addItem(poly)
                self.scene.polygon_items.append(poly)
                for p in points:
                    poly.addPointLast(QtCore.QPointF(p[0], p[1]))

    def completeLastMask(self):
        # 返回最后一个标签是否完成，false就是还有带点的
        if not self.controller:
            return True
        if not self.controller.is_incomplete_mask:
            return True
        res = self.warn(
            self.trans.put("完成最后一个目标？"),
            self.trans.put("是否完成最后一个目标的标注，不完成不会进行保存。"),
            QMessageBox.Yes | QMessageBox.Cancel,
        )
        if res == QMessageBox.Yes:
            self.finishObject()
            self.setDirty()
            return True
        return False

    def saveLabel(self, saveAs=False, savePath=None):
        # 1. 需要处于标注状态
        if not self.controller or self.controller.image is None:
            return
        # 2. 完成正在交互式标注的标签
        self.completeLastMask()
        # 3. 确定保存路径
        if not savePath:
            # 3.1 指定了标签文件夹，而且不是另存为：根据标签文件夹和文件名出保存路径
            if not saveAs and self.outputDir is not None:
                if osp.exists(self.outputDir) == False:
                    os.mkdir(self.outputDir)
                name, ext = osp.splitext(osp.basename(self.imagePath))
                if not self.origExt:
                    ext = ".png"
                savePath = osp.join(
                    self.outputDir,
                    name + ext,
                    # ".".join((os.path.basename(self.imagePath).split(".")[0:-1]))
                )
                print("save path", savePath)
            else:
                filters = "Label files (*.png)"
                dlg = QtWidgets.QFileDialog(
                    self,
                    self.trans.put("保存标签文件路径"),
                    osp.dirname(self.imagePath),
                    filters,
                )
                dlg.setDefaultSuffix("png")
                dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
                dlg.setOption(QtWidgets.QFileDialog.DontConfirmOverwrite, False)
                dlg.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, False)
                savePath, _ = dlg.getSaveFileName(
                    self,
                    self.trans.put("选择标签文件保存路径"),
                    ".".join((os.path.basename(self.imagePath).split(".")[0:-1]))
                    + ".png",
                )
        if savePath is None or not osp.exists(osp.dirname(savePath)):
            return
        # 是否保存伪彩色
        if self.save_status[0]:
            # 保存带有调色板的
            # TODO：关于linux保存bug还需要进一步检测修改
            mask_pil = Image.fromarray(self.controller.result_mask, "P")
            mask_map = [0, 0, 0]
            for lb in self.labelList:
                mask_map += lb.color
            mask_pil.putpalette(mask_map)
            mask_pil.save(savePath)
        else:
            # cv2.imwrite(savePath, self.controller.result_mask)
            # 保存路径带有中文
            cv2.imencode(".png", self.controller.result_mask)[1].tofile(savePath)
        if savePath not in self.labelPaths:
            self.labelPaths.append(savePath)
        # 是否保存json
        if self.save_status[1]:
            polygons = self.scene.polygon_items
            labels = []
            for polygon in polygons:
                l = self.labelList[polygon.labelIndex]
                label = {
                    "name": l.name,
                    "labelIdx": l.idx,
                    "color": l.color,
                    "points": [],
                }
                poly = polygon.polygon()
                for p in poly:
                    label["points"].append([p.x(), p.y()])
                labels.append(label)
            savePath = savePath[: -len("png")] + "json"
            open(savePath, "w", encoding="utf-8").write(json.dumps(labels))
        self.setClean()
        self.statusbar.showMessage(self.trans.put("标签成功保存至") + " " + savePath)

    def setClean(self):
        self.isDirty = False

    def setDirty(self):
        self.isDirty = True

    def changeOutputDir(self, dir=None):
        if dir is None:
            outputDir = QtWidgets.QFileDialog.getExistingDirectory(
                self,
                self.trans.put("选择标签保存路径") + " - " + __APPNAME__,
                "/home/lin/Desktop/output/",
                QtWidgets.QFileDialog.ShowDirsOnly
                | QtWidgets.QFileDialog.DontResolveSymlinks,
            )
        else:
            outputDir = dir
        if len(outputDir) == 0 or not osp.exists(outputDir):
            return False
        labelPaths = os.listdir(outputDir)
        exts = ["png"]
        labelPaths = [n for n in labelPaths if n.split(".")[-1] in exts]
        labelPaths = [osp.join(outputDir, n) for n in labelPaths]
        self.outputDir = outputDir
        self.labelPaths = labelPaths
        print("labelpaths:", self.labelPaths)
        # 加载对应的标签列表
        lab_auto_save = osp.join(self.outputDir, "autosave_label.txt")
        if osp.exists(lab_auto_save) == False:
            lab_auto_save = osp.join(self.outputDir, "label/autosave_label.txt")
        print("lab_auto_save:", lab_auto_save)
        if osp.exists(lab_auto_save):
            try:
                self.loadLabelList(lab_auto_save)
            except:
                pass
        return True

    def maskOpacityChanged(self):
        self.sldOpacity.textLab.setText(str(self.opacity))
        if not self.controller or self.controller.image is None:
            return
        for polygon in self.scene.polygon_items:
            polygon.setOpacity(self.opacity)
        self._update_image()

    def clickRadiusChanged(self):
        self.sldClickRadius.textLab.setText(str(self.clickRadius))
        if not self.controller or self.controller.image is None:
            return
        self._update_image()

    def threshChanged(self):
        self.sldThresh.textLab.setText(str(self.segThresh))
        if not self.controller or self.controller.image is None:
            return
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
        if not self.controller or self.controller.image is None:
            return
        self.controller.reset_last_object()
        self.setClean()

    def redoClick(self):
        if self.image is None:
            return
        if not self.controller:
            return
        self.controller.redo_click()

    def canvasClick(self, x, y, isLeft):
        if self.controller is None:
            return
        if self.controller.image is None:
            return
        currLabel = self.controller.curr_label_number
        if not currLabel or currLabel == 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle(self.trans.put("未选择当前标签"))
            msg.setText(self.trans.put("请先在标签列表中单击点选标签"))
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
        self.annImage.setPixmap(QPixmap(image))

        # BUG: 一直有两张图片在scene里，研究是为什么
        # print(self.scene.items())

    def viewZoomed(self, scale):
        self.scene.scale = scale
        self.scene.updatePolygonSize()

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
        self.scene.scale = self.canvas.zoom_all

    def queueEvent(self, function):
        # TODO: 研究这个东西是不是真的不影响ui
        QtCore.QTimer.singleShot(0, function)

    def toggleAutoSave(self, save):
        if save and not self.outputDir:
            self.changeOutputDir(None)
        if save and not self.outputDir:
            save = False
        self.actions.auto_save.setChecked(save)
        self.settings.setValue("auto_save", save)

    def changeSave(self, index):
        self.save_status[index] = bool(self.save_status[index] - 1)

    def changeWorkerShow(self, index):
        # 检测遥感所需的gdal环境
        if index == 4:
            if check_gdal() == False:
                self.warn(
                    self.trans.put("无法导入GDAL"),
                    self.trans.put("请检查环境中是否存在GDAL，若不存在则无法使用遥感工具！"),
                    QMessageBox.Yes,
                )
                self.statusbar.showMessage(self.trans.put("打开失败，未检出GDAL"))
                return
        self.workers_show[index] = bool(self.workers_show[index] - 1)
        self.refreshWorker()

    def rsBandSet(self, idx):
        for i in range(len(self.bandCombos)):
            self.rsRGB[i] = self.bandCombos[i].currentIndex()
        self.image = selec_band(self.rawimg, self.rsRGB)
        image = (
            self.image
        )  # if self.rsShow.currentIndex() == 0 else twoPercentLinear(self.image)
        self.controller.image = image
        self._update_image()

    def refreshWorker(self, is_init=False):
        if is_init == True:
            if self.workerStatus != []:
                self.workers_show = [strtobool(w) for w in self.workerStatus]
            for i in range(len(self.menus.showMenu)):
                self.menus.showMenu[i].setChecked(bool(self.workers_show[i]))
        else:
            self.settings.setValue("worker_status", self.workers_show)
        for t, w in zip(self.workers_show, self.workers):
            if t == True:
                w.show()
            else:
                w.hide()

    # def rsShowModeChange(self, idx):
    #     if not self.controller or self.controller.image is None:
    #         return
    #     # if idx == 1:
    #     #     self.controller.image = twoPercentLinear(self.image)
    #     # else:
    #     self.controller.image = self.image
    #     self._update_image()

    def update_bandList(self):
        bands = self.rawimg.shape[-1] if len(self.rawimg.shape) == 3 else 1
        for i in range(len(self.bandCombos)):
            self.bandCombos[i].currentIndexChanged.disconnect()
            self.bandCombos[i].clear()
            self.bandCombos[i].addItems([("band_" + str(j + 1)) for j in range(bands)])
            try:
                self.bandCombos[i].setCurrentIndex(self.rsRGB[i])
            except IndexError:
                pass
        for bandCombo in self.bandCombos:
            bandCombo.currentIndexChanged.connect(self.rsBandSet)  # 设置波段

    def toggleLargestCC(self, on):
        try:
            self.controller.filterLargestCC = on
        except:
            pass

    def setLanguage(self):
        tmp = bool(strtobool(self.settings.value("language_state")) - 1)
        self.settings.setValue("language_state", tmp)

    @property
    def opacity(self):
        return self.sldOpacity.value() / 100

    @property
    def clickRadius(self):
        return self.sldClickRadius.value()

    @property
    def segThresh(self):
        return self.sldThresh.value() / 100

    def warn(self, title, text, buttons=QMessageBox.Yes):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(buttons)
        return msg.exec_()

    def toBeImplemented(self):
        self.statusbar.showMessage(self.trans.put("功能尚在开发"))

    def showShortcuts(self):
        self.toBeImplemented()

    # 加载界面
    def loadLayout(self):
        self.restoreState(self.layoutStatus)
        print("Load Layout")

    def closeEvent(self, event):
        # 保存界面
        self.settings.setValue("layout_status", QByteArray(self.saveState()))
        # 如果设置了保存路径，把标签也保存下
        if self.outputDir is not None:
            self.saveLabelList(osp.join(self.outputDir, "autosave_label.txt"))
            print("autosave label finished!")
        # 关闭主窗体退出程序，子窗体也关闭
        sys.exit(0)
