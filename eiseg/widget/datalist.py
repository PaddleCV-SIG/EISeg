"""
widget = QtWidgets.QWidget()
horizontalLayout = QtWidgets.QHBoxLayout(widget)
ListRegion = QtWidgets.QVBoxLayout()
ListRegion.setObjectName("ListRegion")
# labFiles = self.create_text(CentralWidget, "labFiles", "数据列表")
# ListRegion.addWidget(labFiles)
self.listFiles = QtWidgets.QListWidget(CentralWidget)
self.listFiles.setObjectName("ListFiles")
ListRegion.addWidget(self.listFiles)
horizontalLayout.addLayout(ListRegion)
self.DataDock = p_create_dock("DataDock", self.tr("数据列表"), widget)
MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.DataDock)

"""

from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt

import dock


class FileList(dock.DockWidget):
    def __init__(self):
        pass
