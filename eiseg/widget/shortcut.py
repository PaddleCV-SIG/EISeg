import math

from qtpy import QtWidgets
from qtpy.QtWidgets import QLabel, QPushButton, QGridLayout


class ShortcutWindow(QtWidgets.QWidget):
    def __init__(self, actions):
        super().__init__()
        print("init", len(actions))
        self.actions = actions
        self.initUI()

    def initUI(self):
        grid = QGridLayout()
        self.setLayout(grid)

        actions = self.actions
        print(len(actions))
        rows = math.ceil(len(actions) / 2)

        for idx, action in enumerate(actions):
            print(idx, action.data())
            grid.addWidget(QLabel(action.iconText()[1:]), idx // 2, idx % 2 * 2)
            grid.addWidget(
                QPushButton(action.shortcut().toString()),
                idx // 2,
                idx % 2 * 2 + 1,
            )
        self.setWindowTitle("编辑快捷键")
