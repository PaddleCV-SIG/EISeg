from qtpy import QtWidgets


class DockWidget(QtWidgets.QDockWidget):
    def __init__(self, parent, name, text):
        # super().__init__(parent=parent)
        super().__init__()
        # self.setObjectName(name)
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        # 感觉不给关闭好点。可以在显示里面取消显示。有关闭的话显示里面的enable还能判断修改，累了
        self.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable
        )
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMinimumWidth(230)
        # self.setWindowTitle(text)
        self.setStyleSheet("QDockWidget { background-color:rgb(204,204,248); }")
        self.topLevelChanged.connect(self.changeBackColor)

    def changeBackColor(self, isFloating):
        if isFloating:
            self.setStyleSheet("QDockWidget { background-color:rgb(255,255,255); }")
        else:
            self.setStyleSheet("QDockWidget { background-color:rgb(204,204,248); }")
