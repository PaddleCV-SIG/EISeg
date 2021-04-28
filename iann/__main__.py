import sys
from PyQt5.QtWidgets import QApplication  # 导入PyQt相关模块
from app import APP_IANN   # 导入带槽的界面


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWin = APP_IANN()  # 创建对象
    # myWin.show()  # 显示窗口
    myWin.showMaximized()  # 全屏显示窗口
    sys.exit(app.exec_())