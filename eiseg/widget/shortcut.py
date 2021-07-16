import os.path as osp
import math
from functools import partial

from qtpy import QtCore, QtWidgets
from qtpy.QtWidgets import (
    QLabel,
    QPushButton,
    QGridLayout,
    QVBoxLayout,
    QDesktopWidget,
    QMessageBox,
)
from qtpy.QtGui import QKeySequence, QIcon
from qtpy import QtCore
from qtpy.QtCore import Qt

from util import save_configs


class RecordShortcutWindow(QtWidgets.QKeySequenceEdit):
    def __init__(self, finishCallback):
        super().__init__()
        self.finishCallback = finishCallback
        # self.setWindowTitle("输入快捷键")
        # 隐藏界面
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.show()
        self.editingFinished.connect(lambda: finishCallback(self.keySequence()))

    def keyReleaseEvent(self, ev):
        self.finishCallback(self.keySequence())


class ShortcutWindow(QtWidgets.QWidget):
    def __init__(self, actions, pjpath):
        super().__init__()
        self.setWindowTitle("编辑快捷键")
        self.setWindowIcon(QIcon(osp.join(pjpath, "resource/Shortcut.png")))
        self.setFixedSize(self.width(), self.height()); 
        self.actions = actions
        self.recorder = None
        self.initUI()

    def initUI(self):
        grid = QGridLayout()
        self.setLayout(grid)

        actions = self.actions
        for idx, action in enumerate(actions):
            grid.addWidget(QLabel(action.iconText()[1:]), idx // 2, idx % 2 * 2)
            shortcut = action.shortcut().toString()
            if len(shortcut) == 0:
                shortcut = "无"
            button = QPushButton(shortcut)
            button.setFixedWidth(150)
            button.setFixedHeight(30)
            button.clicked.connect(partial(self.recordShortcut, action))
            grid.addWidget(
                button,
                idx // 2,
                idx % 2 * 2 + 1,
            )

    def refreshUi(self):
        actions = self.actions
        for idx, action in enumerate(actions):
            shortcut = action.shortcut().toString()
            if len(shortcut) == 0:
                shortcut = "无"
            self.layout().itemAtPosition(
                idx // 2,
                idx % 2 * 2 + 1,
            ).widget().setText(shortcut)

    def recordShortcut(self, action):
        # 打开快捷键设置的窗口时，如果之前的还在就先关闭
        if self.recorder is not None:
            self.recorder.close()
        self.recorder = RecordShortcutWindow(self.setShortcut)
        self.currentAction = action

    def setShortcut(self, key):
        print("setting shortcut", key.toString())
        self.recorder.close()

        for a in self.actions:
            if a.shortcut() == key:
                key = key.toString()
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle(f"{key}快捷键冲突")
                msg.setText(f"{key}快捷键已被{a.data()}使用，请设置其他快捷键或先修改{a.data()}的快捷键")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
                return
        self.currentAction.setShortcut(key)
        self.refreshUi()
        save_configs(None, None, self.actions)

    def closeEvent(self, event):
        # 关闭时也退出快捷键设置
        self.recorder.close()