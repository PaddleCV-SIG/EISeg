import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QDockWidget, QTextEdit


class Demo(QMainWindow):
    def __init__(self):
        super(Demo, self).__init__()
        # 1
        self.dock1 = QDockWidget('Dock Window 1', self)
        self.dock2 = QDockWidget('Dock Window 2', self)
        self.dock3 = QDockWidget('Dock Window 3', self)

        # 2
        self.dock1.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.dock2.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.dock3.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        # 3
        self.dock1.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
        self.dock2.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
        self.dock3.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)

        # 4
        self.text1 = QTextEdit()
        self.text2 = QTextEdit()
        self.text3 = QTextEdit()

        self.dock1.setWidget(self.text1)
        self.dock2.setWidget(self.text2)
        self.dock3.setWidget(self.text3)

        # 5
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock1)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock2)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock3)

        # 6
        self.center_text = QTextEdit()
        self.setCentralWidget(self.center_text)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    demo = Demo()
    demo.show()
    sys.exit(app.exec_())